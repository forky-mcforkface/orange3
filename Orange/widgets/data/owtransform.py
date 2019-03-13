from typing import Optional

import numpy as np

from Orange.data import Table, Domain
from Orange.widgets import gui
from Orange.widgets.report.report import describe_data
from Orange.widgets.settings import Setting
from Orange.widgets.utils.sql import check_sql_input
from Orange.widgets.utils.widgetpreview import WidgetPreview
from Orange.widgets.widget import OWWidget, Input, Output, Msg


class OWTransform(OWWidget):
    name = "Transform"
    description = "Transform data table."
    icon = "icons/Transform.svg"
    priority = 2110
    keywords = []

    retain_all_data = Setting(False)

    class Inputs:
        data = Input("Data", Table, default=True)
        template_data = Input("Template Data", Table)

    class Outputs:
        transformed_data = Output("Transformed Data", Table)

    class Error(OWWidget.Error):
        error = Msg("An error occurred while transforming data.\n{}")

    resizing_enabled = False
    want_main_area = False

    def __init__(self):
        super().__init__()
        self.data = None  # type: Optional[Table]
        self.template_domain = None  # type: Optional[Domain]
        self.transformed_info = describe_data(None)  # type: OrderedDict

        info_box = gui.widgetBox(self.controlArea, "Info")
        self.input_label = gui.widgetLabel(info_box, "")
        self.template_label = gui.widgetLabel(info_box, "")
        self.output_label = gui.widgetLabel(info_box, "")
        self.set_input_label_text()
        self.set_template_label_text()

        box = gui.widgetBox(self.controlArea, "Output")
        gui.checkBox(box, self, "retain_all_data", "Retain all data",
                     callback=self.apply)

    def set_input_label_text(self):
        text = "No data on input."
        if self.data:
            text = "Input data with {:,} instances and {:,} features.".format(
                len(self.data),
                len(self.data.domain.attributes))
        self.input_label.setText(text)

    def set_template_label_text(self):
        text = "No template data on input."
        if self.data and self.template_domain is not None:
            text = "Template domain applied."
        elif self.template_domain is not None:
            text = "Template data includes {:,} features.".format(
                len(self.template_domain.attributes))
        self.template_label.setText(text)

    def set_output_label_text(self, data):
        text = ""
        if data:
            text = "Output data includes {:,} features.".format(
                len(data.domain.attributes))
        self.output_label.setText(text)

    @Inputs.data
    @check_sql_input
    def set_data(self, data):
        self.data = data
        self.set_input_label_text()

    @Inputs.template_data
    @check_sql_input
    def set_template_data(self, data):
        self.template_domain = data and data.domain

    def handleNewSignals(self):
        self.apply()

    def apply(self):
        self.clear_messages()
        transformed_data = None
        if self.data and self.template_domain is not None:
            try:
                transformed_data = self.data.transform(self.template_domain)
            except Exception as ex:  # pylint: disable=broad-except
                self.Error.error(ex)

        data = transformed_data
        if data and self.retain_all_data:
            data = self.merged_data(data)
        self.transformed_info = describe_data(data)
        self.Outputs.transformed_data.send(data)
        self.set_template_label_text()
        self.set_output_label_text(data)

    def merged_data(self, t_data):
        domain = self.data.domain
        t_domain = t_data.domain
        metas = domain.metas + t_domain.attributes + t_domain.metas
        domain = Domain(domain.attributes, domain.class_vars, metas)
        data = self.data.transform(domain)
        metas = np.hstack((t_data.X, t_data.metas))
        data.metas[:, -metas.shape[1]:] = metas
        return data

    def send_report(self):
        if self.data:
            self.report_data("Data", self.data)
        if self.template_domain is not None:
            self.report_domain("Template data", self.template_domain)
        if self.transformed_info:
            self.report_items("Transformed data", self.transformed_info)


if __name__ == "__main__":  # pragma: no cover
    from Orange.preprocess import Discretize

    table = Table("iris")
    WidgetPreview(OWTransform).run(
        set_data=table, set_template_data=Discretize()(table))
