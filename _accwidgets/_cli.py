import argparse
import accwidgets


def run():
    """Run accwidgets CLI utility and parse command-line arguments."""
    logo = """

   █████╗  ██████╗ ██████╗██╗    ██╗██╗██████╗  ██████╗ ███████╗████████╗███████╗
  ██╔══██╗██╔════╝██╔════╝██║    ██║██║██╔══██╗██╔════╝ ██╔════╝╚══██╔══╝██╔════╝
  ███████║██║     ██║     ██║ █╗ ██║██║██║  ██║██║  ███╗█████╗     ██║   ███████╗
  ██╔══██║██║     ██║     ██║███╗██║██║██║  ██║██║   ██║██╔══╝     ██║   ╚════██║
  ██║  ██║╚██████╗╚██████╗╚███╔███╔╝██║██████╔╝╚██████╔╝███████╗   ██║   ███████║
  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══╝╚══╝ ╚═╝╚═════╝  ╚═════╝ ╚══════╝   ╚═╝   ╚══════╝
    """
    common_parser_args = {
        "add_help": False,  # Will be added manually (with consistent formatting)
        "formatter_class": argparse.RawDescriptionHelpFormatter,
    }

    parser = argparse.ArgumentParser(description=logo + "\n\n" + (accwidgets.__doc__ or ""), **common_parser_args)
    parser.add_argument("-V", "--version",
                        action="version",
                        version=accwidgets.__version__,
                        help="Show accwidgets' version number and exit.")

    _install_help(parser)

    subparsers = parser.add_subparsers(dest="cmd")
    app_parser = subparsers.add_parser("designer-paths",
                                       help="Collect all accwidgets Qt Designer plugin paths and print it.\n",
                                       description="  Collect all accwidgets Qt Designer plugin paths and print it.\n"
                                                   "\n"
                                                   "  This command looks for all available Qt Designer plugins\n"
                                                   "  brought by accwidgets library and gathers them into a single\n"
                                                   "  string, so that they can be injected into Qt Designer with a\n"
                                                   "  single line command, e.g.\n"
                                                   '  "PYQTDESIGNERPATH=$(accwidgets-cli designer-paths) designer".\n'
                                                   "\n"
                                                   "  It is very handy to create an alias (e.g. for the virtual\n"
                                                   "  environment, where accwidgets is installed) so that plugins\n"
                                                   "  are always injected in Qt Designer. For instance:\n"
                                                   "  alias designer='PYQTDESIGNERPATH=$(accwidgets-cli designer-paths):$PYQTDESIGNERPATH designer'\n"
                                                   "  It can be placed to virtual environment's \"bin/activate\"\n"
                                                   "  script, or user's \"~/.bashrc\" file, so that it always\n"
                                                   "  overwrites the original command.",
                                       **common_parser_args)
    _collect_subcommand(app_parser)

    tmpl_parser = subparsers.add_parser("install-templates",
                                        help="Install additional templates to current user's Qt Designer "
                                             "configuration.",
                                        description="  Install additional templates brought by accwidgets library\n"
                                                    "  to current user's Qt Designer configuration.\n"
                                                    "\n"
                                                    "  New templates may contain widgets from accwidgets library.\n"
                                                    "  Therefore, after installing these templates, if Qt Designer\n"
                                                    "  gets launched outside of virtual environment, where \n"
                                                    "  accwidgets have been installed, or if PYQTDESIGNERPATH is\n"
                                                    '  not set properly (see "designer-paths" command), you may\n'
                                                    "  receive warnings about missing attributes.",
                                        **common_parser_args)
    _templates_subcommand(tmpl_parser)

    tmpl_parser = subparsers.add_parser("uninstall-templates",
                                        help="Remove custom templates that have been installed with\n"
                                             '"install-templates" command.',
                                        description='  This command undoes changes performed by "install-templates"'
                                                    "  in the past.",
                                        **common_parser_args)
    _templates_subcommand(tmpl_parser)

    args = parser.parse_args()

    if args.cmd == "designer-paths":
        from ._designer_tools import collect_paths
        collect_paths()
    elif args.cmd == "install-templates":
        from ._designer_tools import install_additional_templates
        install_additional_templates()
    elif args.cmd == "uninstall-templates":
        from ._designer_tools import uninstall_additional_templates
        uninstall_additional_templates()
    else:
        parser.print_help()


def _install_help(parser: argparse._ActionsContainer):
    parser.add_argument("-h", "--help",
                        action="help",
                        help="Show this help message and exit.")


def _collect_subcommand(parser: argparse.ArgumentParser):
    _install_help(parser)


def _templates_subcommand(parser: argparse.ArgumentParser):
    _install_help(parser)
