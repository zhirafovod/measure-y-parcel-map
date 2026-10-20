import json
RES={'Single Family Home','Single Family Home w/ ADU','Single Family Home - BMR','2-Units','3-Units','4-Units',
 'Apartment - Small (5-19 Units)','Apartment - Mid (20-49 Units)','Apartment - Large (50+ Units)','Apartment',
 'Condominium','Condominium - BMR','Townhome','SFR Converted to 2-Units','More than One Detached Living Unit',
 'Residential; Combination of Unit Types','Residential Miscellaneous','Independent Living Facility'}
EXEMPT_PUC={'Park','Highway & Streets','Right-of-Way','Pipeline/Canal','Underwater & Marshland','Post Office','Community Center'}
MAYBE={'School','Church','College','Educational Facility','Cemetery','Nursing, Convalescent Home','Skilled Nursing Facility','Assisted Living Facility'}
SFR_GARAGE={'Single Family Home','Single Family Home w/ ADU','Single Family Home - BMR'}
def classify(pucdesc, owner_kind):
    if not isinstance(pucdesc,str): pucdesc=None
    else: pucdesc=pucdesc.replace(' (Migrated)','')
    if owner_kind: return 'exempt', 'Public agency ('+owner_kind+')'
    if pucdesc in EXEMPT_PUC: return 'exempt', pucdesc
    if pucdesc in MAYBE: return 'maybe', pucdesc
    if pucdesc in RES: return 'res', pucdesc
    if pucdesc is None: return 'unk', 'No use code'
    if pucdesc.startswith('Vacant'): return 'other', pucdesc
    return 'other', pucdesc
