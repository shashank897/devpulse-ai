from functools import lru_cache
@lru_cache(maxsize=1)
def load_model(path):
    import joblib
    # Deployment-controlled artifact only; never accept an uploaded pickle/joblib.
    return joblib.load(path)
def predict_code(code,path):
    artifact=load_model(path);score=float(artifact['model'].predict_proba([code])[0,1])
    threshold=float(artifact['metadata'].get('threshold',.5))
    return {'model_name':artifact['metadata']['model'],'model_version':artifact['metadata']['version'],'raw_score':score,'threshold':threshold,'calibrated_probability':None,'prediction':'elevated_defect_signal' if score>=threshold else 'low_defect_signal','limitations':['Experimental C/C++ function-level classification.','Raw model output is not a verified vulnerability probability.','Not a security certification.']}
