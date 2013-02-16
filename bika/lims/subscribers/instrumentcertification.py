from Products.CMFCore.utils import getToolByName
from bika.lims.subscribers import doActionFor
from Products.ATContentTypes.utils import DT2dt
from datetime import datetime
from bika.lims.content.instrument import Instrument


def MovedEventHandler(instance, event):
    """ Triggered when the InstrumentCertification is removed/moved/added

    If the instrument is moved to another Instrument, checks the certification
    status for the new one and if needed, modifies it to 'Certified' and sets
    its CurrentCertification value.

    """
    old = event.oldParent
    new = event.newParent
    if old is not None and isinstance(old, Instrument) and old != new:
        if old.getCurrentCertificationUID() == instance.UID():
            old.setCurrentCertificationUID(None)


def ModifiedEventHandler(instance, event):
    """ Triggered when the InstrumentCertification is modified

    Checks if the instrument state and CurrentCertification value should be
    changed according to the InstrumentCertification object. Sets the status of
    the parent Instrument to 'Uncertified' if the InstrumentCertification is
    the current certificate for that Instrument and the current date is out of
    range according to ValidTo and ValidFrom fields.

    """
    instrument = instance.aq_parent
    wf = getToolByName(instance, 'portal_workflow')
    if instrument.getCurrentCertification() and \
        instrument.getCurrentCertification().UID() == instance.UID():
        now = datetime.now()
        validfrom = DT2dt(instance.getValidFrom()).replace(tzinfo=None)
        validto = DT2dt(instance.getValidTo()).replace(tzinfo=None)
        if now < validfrom or now > validto:
            instrument.setCurrentCertificationUID(None)
            doActionFor(instrument, 'uncertify')

    elif wf.getInfoFor(instrument, 'certification_state') == 'uncertified':
        now = datetime.now()
        validfrom = DT2dt(instance.getValidFrom()).replace(tzinfo=None)
        validto = DT2dt(instance.getValidTo()).replace(tzinfo=None)
        if now >= validfrom and now <= validto:
            instrument.setCurrentCertificationUID(instance.UID())
            doActionFor(instrument, 'certify')
