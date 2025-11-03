from .CHTElement import CHTElement


class CHTFormSQLComparator:
    """A class for comparing json extraction SQL queries from CHT forms."""
    def __init__(
            self,
            sql_file_path: str,
            xlsform_path: str,
            founds: list[CHTElement] = [],
            not_founds: list[CHTElement] = [],
            found_data: list[dict] = []
    ):
        self.sql_file_path = sql_file_path
        self.xlsform_path = xlsform_path
        self.founds = founds
        self.found_data = found_data
        self.not_founds = not_founds
        self.all_elements = CHTElement.get_question_paths(xlsform_path)
        self._compare()


    def _compare(self):
        """Compares SQL queries from CHT forms with JSON extraction."""
        for element in self.all_elements:
            if element.json_path:
                sql_refs = element.find_sql_references(self.sql_file_path)
                if sql_refs and sql_refs['count'] > 0:
                    self.founds.append(element)
                    self.found_data.append(sql_refs)
                else:
                    self.not_founds.append(element)

    def print(self):
        """Prints the results of the comparison."""
        print(f"\n--- SQL References in {self.sql_file_path} ---")
        for element in self.founds:
            print(f"- Element '{element.question_name}' ({element.json_path}):")
            print(f"  Found {self.found_data[self.founds.index(element)]['count']} times on lines: {self.found_data[self.founds.index(element)]['lines']}")

        print(f"\n--- {len(self.not_founds)} Not Found Elements ---")
        input_group = CHTElement(
                question_name="",
                group=True,
                odk_type="begin group",
                path="/" + element.form_id() + "/inputs",
                excel_line_number=0
            )
        prescription_group = CHTElement(
                question_name="",
                group=True,
                odk_type="begin group",
                path="/" + element.form_id() + "/fields/prescription_summary",
                excel_line_number=0
        )
        for element in self.not_founds:
            if element < input_group or element < prescription_group:
                continue

            print(f"- Element '{element.question_name}' ({element.json_path}):")
