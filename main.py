import sys
from containers import Container

def main():
    """
    This is the application's main entry point (Composition Root).
    It initializes the dependency injection container and runs the selected UI.
    """
    # 1. Create and configure the container
    container = Container()
    container.config.from_yaml('config.yml')
    container.form_context_config.from_yaml('form_context.yml')

    # 2. Get a logger and handle potential startup errors
    try:
        logger = container.logger()
        logger.log_info("Application starting up...")
    except Exception as e:
        print(f"A critical error occurred during logger initialization: {e}", file=sys.stderr)
        sys.exit(1)

    # 3. Run the selected UI
    # The container's `build_ui` provider is a pre-configured callable
    # that already has all its dependencies injected.
    try:
        container.build_ui()
        logger.log_info("Application finished.")
    except Exception as e:
        logger.log_exception(f"A critical error occurred while running the UI: {e}")
        print(f"A critical error occurred: {e}", file=sys.stderr)
        sys.exit(1)

# This script is designed to be run by either `python main.py` or `streamlit run main.py`.
# In both cases, we just need to call main(). The container handles the UI switching.
main()
