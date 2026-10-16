from app.validation import abv, amount, validate, normalize

def test_abv_proof():
    assert abv('90 Proof') == 45
    assert abv('45% Alc./Vol.') == 45

def test_volume():
    assert amount('0.75 L') == 750
    assert amount('750 mL') == 750

def test_brand_case():
    x=validate({'brand':"Stone's Throw"},["STONE'S THROW"])
    assert x['checks'][0]['status']=='match'

def test_numeric_mismatch():
    x=validate({'abv':'45%'},['40% Alc./Vol.'])
    assert next(c for c in x['checks'] if c['field']=='abv')['status']=='mismatch'

def test_missing_warning_requires_review():
    x=validate({},['random text'])
    assert x['checks'][-1]['status']=='manual_review'
