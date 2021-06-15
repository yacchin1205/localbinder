import asyncio
import json
from pathlib import Path
import re

from traitlets import Int, Unicode, List
from traitlets.config import Application
from binderhub.app import BinderHub

from localbinder.url import parse_binder_url
from localbinder.exceptions import Repo2DockerError, DockerError

async def _read_stream(stream, cb):
    while True:
        line = await stream.readline()
        if line:
            cb(line)
        else:
            break

class LocalBinder(Application):

    aliases = {
        'log-level': 'Application.log_level',
        'f': 'LocalBinder.config_file',
        'config': 'LocalBinder.config_file',
        'port': 'LocalBinder.port',
        'home': 'LocalBinder.home',
    }

    flags = {'debug': ({'Application': {'log_level': 10}}, 'Set loglevel to DEBUG')}

    port = Int(8888, help='Port to listen jupyter notebook server').tag(config=True)

    docker_command = Unicode('docker', help='Docker Command').tag(config=True)

    docker_args = List(['--rm'], help='Additional Arguments for docker command').tag(config=True)

    repo2docker_command = Unicode('repo2docker', help='repo2docker Command').tag(config=True)

    repo2docker_args = List([], help='Additional Arguments for repo2docker command').tag(config=True)

    image_name = Unicode('yacchin1205/localbinder/r2d-image', help='Image name to save').tag(config=True)

    home = Unicode(help='Local directory for home (must be an absolute path)').tag(config=True)

    config_file = Unicode('', help="Load this config file").tag(config=True)

    name = 'localbinder'
    description = 'Running binder container on localhost'

    def initialize(self, argv=None):
        self.parse_command_line(argv)
        if self.config_file:
            self.load_config_file(self.config_file)

    def start(self):
        self.docker_process = None
        try:
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._run())
        except KeyboardInterrupt:
            self.cleanup()

    def cleanup(self):
        if self.docker_process:
            self.docker_process.terminate()

    @property
    def url(self):
        if len(self.extra_args) != 1:
            raise ValueError(f'Only one URL can be specified: {self.extra_args}')
        return self.extra_args[0]

    async def _run(self):
        self.log.info("app.config:")
        self.log.info(self.config)
        binderhub = BinderHub(config=self.config)
        self.log.info(binderhub.repo_providers)
        binder_url = parse_binder_url(self.url)
        if binder_url is None:
            self.log.info(f'Not binder URL: {self.url}')
            await self._start_notebook(self.url)
            return
        repo, spec = binder_url
        self.log.info(f'Binder URL: {repo}, {spec}')
        if repo not in binderhub.repo_providers:
            self.log.warn(f'Provider not found: {repo}')
            await self._start_notebook(self.url)
            return
        provider = binderhub.repo_providers[repo](config=self.config, spec=spec)
        repo_url = self.repo_url = provider.get_repo_url()
        ref = await provider.get_resolved_ref()
        self.log.info(f'Repo URL: {repo_url} ref={ref}')
        await self._start_notebook(repo_url, ref=ref)

    async def _start_notebook(self, repo_url, ref=None):
        image_name = await self._repo2docker(repo_url, ref=ref)
        print(f'Successfully built: {image_name}')
        await self._docker(image_name)

    async def _docker(self, image_name):
        print(f'Running... {image_name}')
        args = ['run', '-p', f'{self.port}:8888', '-i']
        if self.home:
            args += ['-v', f'{self.home}:/home/jovyan']
        args += self.docker_args
        process = await asyncio.create_subprocess_exec(
            self.docker_command,
            *args,
            image_name,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        self.docker_process = process
        stderr = []
        stdout = []
        def stdout_cb(x):
            stdout.append(x)
            self.log.info(f'STDOUT: {x}')
        def stderr_cb(x):
            stderr.append(x)
            m = re.match(r'\s*or\s+(http://127\.0\.0\.1:[0-9]+/\?token=\S+)\s*', x.decode('utf8'))
            if m:
                url = m.group(1)
                print(f'Open: {url}')
                print('Use Control-C to stop this server and shut down all kernels')
            self.log.info(f'STDERR: {x}')
        await asyncio.wait([
            _read_stream(process.stdout, stdout_cb),
            _read_stream(process.stderr, stderr_cb)
        ])
        await process.wait()
        if process.returncode != 0:
            raise DockerError(process.returncode, stdout, stderr)

    async def _repo2docker(self, repo_url, ref=None):
        image_name = self.image_name
        args = ['--no-run', '--json-logs', '--image-name', image_name]
        args += self.repo2docker_args
        if ref:
            args += ['--ref', ref]
        print(f'Building... {repo_url} ref={ref}')
        process = await asyncio.create_subprocess_exec(
            self.repo2docker_command,
            *args,
            repo_url,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stderr = []
        stdout = []
        def stdout_cb(x):
            stdout.append(x)
        def stderr_cb(x):
            stderr.append(x)
            try:
                msg = json.loads(x)
                if 'message' in msg:
                    self.log.info(msg['message'])
                else:
                    self.log.info(msg)
            except json.JSONDecodeError:
                self.log.warning(f'Unexpected message: {x}')
        await asyncio.wait([
            _read_stream(process.stdout, stdout_cb),
            _read_stream(process.stderr, stderr_cb)
        ])
        await process.wait()
        if process.returncode != 0:
            raise Repo2DockerError(process.returncode, stdout, stderr)

        self.log.info(f'[repo2docker exited with {process.returncode}]')
        if stdout:
            self.log.info(f'[stdout]\n{stdout}')
        return image_name
