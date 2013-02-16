from AccessControl import ClassSecurityInfo
from Products.ATContentTypes.content import schemata
from Products.ATContentTypes.utils import DT2dt
from Products.ATExtensions.ateapi import RecordsField
from Products.Archetypes.atapi import *
from Products.Archetypes.references import HoldingReference
from Products.CMFCore.permissions import View, ModifyPortalContent
from Products.CMFCore.utils import getToolByName
from bika.lims import bikaMessageFactory as _
from bika.lims.browser.widgets import DateTimeWidget
from bika.lims.browser.widgets import RecordsWidget
from bika.lims.config import PROJECTNAME
from bika.lims.content.bikaschema import BikaSchema, BikaFolderSchema
from bika.lims.interfaces import IInstrument
from datetime import datetime
from plone.app.folder.folder import ATFolder
from zope.interface import implements

schema = BikaFolderSchema.copy() + BikaSchema.copy() + Schema((
                                     
    ReferenceField('InstrumentType',
        vocabulary='getInstrumentTypes',
        allowed_types=('InstrumentType',),
        relationship='InstrumentInstrumentType',        
        required=1,
        widget=SelectionWidget(
            format='select',
            label=_('Instrument type'),
        ),
    ),
                                     
    ReferenceField('Manufacturer',
        vocabulary='getManufacturers',
        allowed_types=('Manufacturer',),
        relationship='InstrumentManufacturer',
        required=1,
        widget=SelectionWidget(
            format='select',
            label=_('Manufacturer'),
        ),
    ),        
                                     
    ReferenceField('Supplier',
        vocabulary='getSuppliers',
        allowed_types=('Supplier',),
        relationship='InstrumentSupplier',
        required=1,
        widget=SelectionWidget(
            format='select',
            label=_('Supplier'),
        ),
    ),

    StringField('Model',
        widget = StringWidget(
            label = _("Model"),
            description = _("The instrument's model number"),
        )
    ),
                                                                      
    StringField('SerialNo',
        widget = StringWidget(
            label = _("Serial No"),
            description = _("The serial number that uniquely identifies the instrument"),
        )
    ),  

    # Procedures
    TextField('InlabCalibrationProcedure',
        schemata = 'Procedures',
        default_content_type = 'text/x-web-intelligent',
        allowable_content_types = ('text/x-web-intelligent',),
        default_output_type="text/html",
        widget = TextAreaWidget(
            label = _("In-lab calibration procedure"),
            description = _("Instructions for in-lab regular calibration routines intended for analysts"),
        ),
    ),
    TextField('PreventiveMaintenanceProcedure',
        schemata = 'Procedures',
        default_content_type = 'text/x-web-intelligent',
        allowable_content_types = ('text/x-web-intelligent',),
        default_output_type="text/html",
        widget = TextAreaWidget(
            label = _("Preventive maintenance procedure"),
            description = _("Instructions for regular preventive and maintenance routines intended for analysts"),
        ),
    ),   
                                                               
    StringField('DataInterface',
        vocabulary = "getDataInterfacesList",
        widget = ReferenceWidget(
            checkbox_bound = 1,
            label = _("Data Interface"),
            description = _("Select an Import/Export interface for this instrument."),
        ),
    ),
    RecordsField('DataInterfaceOptions',
        type = 'interfaceoptions',
        subfields = ('Key','Value'),
        required_subfields = ('Key','Value'),
        subfield_labels = {'OptionValue': _('Key'),
                           'OptionText': _('Value'),},
        widget = RecordsWidget(
            label = _("Data Interface Options"),
            description = _("Use this field to pass arbitrary parameters to the export/import "
                            "modules."),
        ),
    ),

    StringField('CurrentCertificationUID',
        searchable=True,
        required=0,
        widget=StringWidget(
            visible = False,
            label=_("Certification"),
        )
    ),

))
schema['description'].widget.visible = True
schema['description'].schemata = 'default'

def getDataInterfaces(context):
    """ Return the current list of data interfaces
    """
    from bika.lims.exportimport import instruments
    exims = [('',context.translate(_('None')))]
    for exim_id in instruments.__all__:
        exim = getattr(instruments, exim_id)
        exims.append((exim_id, exim.title))
    return DisplayList(exims)

def getMaintenanceTypes(context):
    types = [('preventive', 'Preventive'),
             ('repair', 'Repair'),
             ('enhance', 'Enhancement')]
    return DisplayList(types);

def getCalibrationAgents(context):
    agents = [('analyst', 'Analyst'),
             ('maintainer', 'Maintainer')]
    return DisplayList(agents);

class Instrument(ATFolder):
    implements(IInstrument)
    security = ClassSecurityInfo()
    displayContentsTab = False
    schema = schema

    _at_rename_after_creation = True
    def _renameAfterCreation(self, check_auto_id=False):
        from bika.lims.idserver import renameAfterCreation
        renameAfterCreation(self)

    def getDataInterfacesList(self):
        return getDataInterfaces(self)
    
    def getScheduleTaskTypesList(self):
        return getMaintenanceTypes(self)
    
    def getMaintenanceTypesList(self):
        return getMaintenanceTypes(self)
    
    def getCalibrationAgentsList(self):
        return getCalibrationAgents(self)
    
    def getManufacturers(self):        
        manufacturers = []
        bsc = getToolByName(self, "bika_setup_catalog")
        for manufacturer in bsc(portal_type = 'Manufacturer',
                                inactive_state = 'active'):
            manufacturers.append([manufacturer.UID, manufacturer.Title])
        manufacturers.sort(lambda x,y:cmp(x[1], y[1]))
        return DisplayList(manufacturers)

    def getSuppliers(self):        
        suppliers = []
        bsc = getToolByName(self, "bika_setup_catalog")
        for supplier in bsc(portal_type = 'Supplier',
                                inactive_state = 'active'):
            suppliers.append([supplier.UID, supplier.getName])
        suppliers.sort(lambda x,y:cmp(x[1], y[1]))        
        return DisplayList(suppliers)
    
    def getInstrumentTypes(self):        
        its = []
        bsc = getToolByName(self, "bika_setup_catalog")
        for it in bsc(portal_type = 'InstrumentType',
                                inactive_state = 'active'):
            its.append([it.UID, it.Title])
        its.sort(lambda x,y:cmp(x[1], y[1]))
        return DisplayList(its)
    
    def getMaintenanceTasks(self):
        return self.objectValues('InstrumentMaintenanceTask')
    
    def getCalibrations(self):
        return self.objectValues('InstrumentCalibration')
    
    def getCertifications(self):
        return self.objectValues('InstrumentCertification')
    
    def getValidations(self):
        return self.objectValues('InstrumentValidation')
    
    def getSchedule(self):
        return self.objectValues('InstrumentScheduledTask')

    def validCertificationAvailable(self):
        """ Returns if the instrument has a valid certification available

        A valid certification is an InstrumentCertification attached to the
        current instance of Instrument with a valid certification date range:
        current date must be between certification Validfrom and ValidTo.
        Ignores the current state of the Instrument (Certified or Uncertified)

        """
        now = datetime.now()
        for cert in self.getCertifications():
            validfrom = DT2dt(cert.getValidFrom()).replace(tzinfo=None)
            validto = DT2dt(cert.getValidTo()).replace(tzinfo=None)
            if now >= validfrom and now <= validto:
                return True
        return False

    def getCurrentCertification(self):
        """ Returns the current certification applied to the instrument
        """
        certUID = self.getCurrentCertificationUID()
        if certUID is not None:
            for cert in self.getCertifications():
                if cert.UID() == certUID:
                    return cert

schemata.finalizeATCTSchema(schema, folderish=True, moveDiscussion=False)

registerType(Instrument, PROJECTNAME)
