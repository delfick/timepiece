from setuptools import setup, find_packages
from timepiece import VERSION

setup(
      name = "timepiece"
    , version = VERSION
    , packages = ['timepiece'] + ['timepiece.%s' % pkg for pkg in find_packages('timepiece')]
    , include_package_data = True

     , install_requires =
       [ 'delfick_error>=1.6'
       , "input_algorithms>=0.5.1"

       , "dateparser==0.4.0"
       , "dateutils==0.6.6"
       , "parsimonious==0.6.2"
       , "aniso8601==1.1.0"
       ]

    , extras_require =
      { "tests":
        [ "nose"
        , "mock"
        , "noseOfYeti"
        ]
      }

    # metadata for upload to PyPI
    , url = "http://timepiece.readthedocs.io"
    , author = "Stephen Moore"
    , author_email = "stephen@delfick.com"
    , description = "Thin DSL for creating time scheduling specifications"
    , license = "MIT"
    , keywords = "scheduling time specification"
    )

