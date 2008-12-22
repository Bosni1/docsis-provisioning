from ProvCon.func import conditionalmethod
import exceptions

__revision__ = "$Revision$"

class BaseForm(object):
    __defaultattrs__ = {        
    }
    def __init__(self, form, *args, **kwargs):
        for kw in self.__defaultattrs__: self.__dict__[kw] = self.__defaultattrs__[kw]
        for kw in kwargs: self.__dict__[kw] = kwargs[kw]
        self.form = form
        self.form.register_event_hook ( "current_record_changed", self._on_record_data_changed )
        self.form.register_event_hook ( "current_record_modified", self._on_record_data_modified )
        self.form.register_event_hook ( "current_record_saved", self._on_record_data_saved )
        
        self.editor_widgets = {}
        
    def create_widget(self):
        self._build_ui()
        
    def _build_ui (self):
        raise NotImplementedError()

    def _create_field_editor (self, field, parent=None, **kwargs):
        creator = self._create_default_field_editor
        if hasattr(self, "_create_field_" + field.table.name + "_" + field.name):
            creator = getattr(self, "_create_field_" + field.table.name + "_" + field.name)
        self.editor_widgets[field.name] = creator(field, parent, **kwargs)
        return self.editor_widgets[field.name]
    
    def _create_default_field_editor (self, field, parent=None, **kwargs):
        raise NotImplementedError()
    
    def _on_record_data_modified (self, record, *args):
        pass
    
    def _on_record_data_saved (self, record, *args):
        pass
        
    def _on_record_data_changed (self, record, *args):
        pass
        
        
        
        
        
        
        