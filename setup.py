from setuptools import setup
def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='ehos',
      version='1.2.0',
      description='Elastic HTCondor OpenStack Scaling',
      url='https://github.com/elixir-no-nels/ehos-python/',
      author='Kim Brugger',
      author_email='kim.brugger@uib.no',
      license='MIT',
      packages=['ehos'],
      install_requires=[
          'htcondor',
          'typing',
          'munch',
          'openstacksdk',
      ],
      classifiers=[
        'Development Status :: 1.0.0',
        'License :: MIT License',
        'Programming Language :: Python :: 3.4'
        ],      
      scripts=['bin/ehosd.py',
               'bin/ehos_deployment.py',
               'bin/ehos_create_config.py',
               'bin/ehos_setup.py',
               'bin/condor_run_jobs.py',
           ],
      # install our config files into an ehos share.
      data_files=[('share/ehos/', ['share/base.yaml',
                                   'share/master.yaml',
                                   'share/execute.yaml',
                                   'share/master.sh',]),
                  ('etc/ehos/', ['etc/ehos.yaml.example',
                                 'etc/ehos.yaml.template']),
                  ('/etc/systemd/system/',['ehos.service'])],
      include_package_data=True,
      zip_safe=False)
