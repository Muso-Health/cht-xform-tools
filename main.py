from containers import Container

def main():
    container = Container()
    container.config.from_yaml('config.yml')
    try:
        logger = container.logger()
        logger.log_info("Application starting up...")

        comparator_service = container.form_comparator_service()
        bulk_audit_service = container.bulk_audit_service()
        xlsform_comparator_service = container.xlsform_comparator_service()
        
        code_repository = container.code_repository()
        cicd_repository = container.cicd_repository()
        data_warehouse_repository = container.data_warehouse_repository()
        xform_api_repository = container.xform_api_repository()

    except Exception as e:
        try:
            container.logger().log_exception(f"A critical error occurred during application initialization: {e}")
        except:
            print(f"A critical error occurred during application initialization: {e}")
        return

    container.build_ui(
        comparator_service=comparator_service,
        bulk_audit_service=bulk_audit_service,
        xlsform_comparator_service=xlsform_comparator_service,
        code_repository=code_repository,
        cicd_repository=cicd_repository,
        data_warehouse_repository=data_warehouse_repository,
        xform_api_repository=xform_api_repository
    )
    
    logger.log_info("Application finished.")

if __name__ == "__main__":
    main()
