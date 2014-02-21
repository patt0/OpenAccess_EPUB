# -*- coding: utf-8 -*-

"""
oaepub convert

Convert explicitly listed articles to EPUB, takes input of XML file, DOI, or URL

Usage:
  convert [--silent | --verbosity=LEVEL] [--epub2 | --epub3] [options] INPUT ...

General Options:
  -h --help             Show this help message and exit
  -v --version          Show program version and exit
  -s --silent           Print nothing to the console during execution
  -V --verbosity=LEVEL  Set how much information is printed to the console
                        during execution (one of: "CRITICAL", "ERROR",
                        "WARNING", "INFO", "DEBUG") [default: INFO]

Convert Specific Options:
  -2 --epub2            Convert to EPUB2
  -3 --epub3            Convert to EPUB3
  --no-cleanup          The EPUB contents prior to .epub-packaging will not be
                        removed
  --no-epubcheck        Disable the use of epubcheck to validate EPUBs
  --no-validate         Disable DTD validation of XML files during conversion.
                        This is only advised if you have pre-validated the files
                        (see 'oaepub validate -h')

Logging Options:
  --no-log-file         Disable logging to file
  -l --log-to=FILE      Specify a single filepath to contain all log data
  --log-level=LEVEL     Set the level for the logging (one of: "CRITICAL",
                        "ERROR", "WARNING", "INFO", "DEBUG") [default: DEBUG]

Convert supports input of the following types:
  XML - Input points to the location of a local XML file (ends with: '.xml')
  DOI - A DOI to be resolved for XML download, if publisher is supported
        (starts with 'doi:')
  URL - A URL link to the article for XML download, if publisher is supported
        (starts with 'http:')

Each individual input will receive its own log (replace '.xml' with '.log')
unless '--log-to' is used to direct all logging information to a specific file
Many default actions for your installation of OpenAccess_EPUB are configurable.
Execute 'oaepub configure' to interactively configure, or modify the config
file manually in a text editor; executing 'oaepub configure where' will tell you
where the config file is located.
"""

#Standard Library modules
import logging
import os
import shutil
import sys

#Non-Standard Library modules
from docopt import docopt

#OpenAccess_EPUB modules
import openaccess_epub.utils
import openaccess_epub.utils.input as input_utils
import openaccess_epub.utils.logs as oae_logging
from openaccess_epub.article import Article


def main(argv=None):
    args = docopt(__doc__,
                  argv=argv,
                  version='OpenAccess_EPUB Docoptify 0.1',
                  options_first=True)

    current_dir = os.getcwd()

    #Basic logging configuration
    oae_logging.config_logging(args['--no-log-file'],
                               args['--log-to'],
                               args['--log-level'],
                               args['--silent'],
                               args['--verbosity'])

    #Get a logger, the 'openaccess_epub' logger was set up above
    command_log = logging.getLogger('openaccess_epub.commands.convert')

    #Load the config module, we do this after logging configuration
    #config = openaccess_epub.utils.load_config_module()

    #Our basic flow is to iterate over the args['INPUT'] list
    for inpt in args['INPUT']:
        #We have to temporarily re-base our log while input utils do some work
        if not args['--no-log-file'] and not args['--log-to']:
            oae_logging.replace_filehandler(logname='openaccess_epub',
                                            new_file='temp.log',
                                            level=args['--log-level'],
                                            frmt=oae_logging.STANDARD_FORMAT)

        command_log.info('Converting input: {0}'.format(inpt))

        #First we need to know the name of the file and where it is
        if inpt.lower().endswith('.xml'):  # This is direct XML file
            root_name = openaccess_epub.utils.file_root_name(inpt)
            abs_input_path = openaccess_epub.utils.get_absolute_path(inpt)
        elif inpt.lower().startswith('doi:'):  # This is a DOI
            root_name = input_utils.doi_input(inpt)
            abs_input_path = os.path.join(current_dir, root_name + '.xml')
        elif inpt.lower().startswith('http:'):  # This is a URL
            root_name = input_utils.url_input(inpt)
            abs_input_path = os.path.join(current_dir, root_name + '.xml')
        else:
            sys.exit('{0} not recognized as XML, DOI, or URL'.format(inpt))

        if not args['--no-log-file'] and not args['--log-to']:
            log_name = root_name + '.log'
            log_path = os.path.join(os.path.dirname(abs_input_path), log_name)
            #Now we move over to the new log file
            shutil.move('temp.log', log_path)
            #And re-base the log file to the new file location
            oae_logging.replace_filehandler(logname='openaccess_epub',
                                            new_file=log_path,
                                            level=args['--log-level'],
                                            frmt=oae_logging.STANDARD_FORMAT)

        #Now that we should be done configuring logging, let's parse the article
        parsed_article = Article(abs_input_path,
                                 validation=not args['--no-validate'])
        #print(parsed_article)

        #Generate the output path name, this will be the directory name for the
        #output. This output directory will later be zipped into an EPUB
        #output_name = os.path.join(utils.get_output_directory(args), raw_name)


#I'm going to mock up the new make_EPUB method here, but it will
#probably belong somewhere else later
def make_EPUB(parsed_article,
              output_directory,
              image_directory,
              config_module=None):
    """
    make_EPUB is used to produce an EPUB file from a parsed article. In addition
    to the article it also requires a path to the appropriate image directory
    which it will insert into the EPUB file, as well the output directory
    location for the EPUB file.

    Parameters:
      article
          An Article object instance
      output_directory
          A directory path where the EPUB will be produced. The EPUB filename
          itself will always be
      image_directory
          A directory path where the EPUB's required image files are stored,
          this directory will be copied into the EPUB.
      config_module=None
          Allows for the injection of a modified or pre-loaded config module. If
          not specified, make_EPUB will load the config file
    """
    pass


if __name__ == '__main__':
    main()