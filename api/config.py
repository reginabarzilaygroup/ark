class Args(object):
    def __init__(self, config_dict):
        self.__dict__.update(config_dict)


class Config(object):
    DEBUG=False
    AGGREGATION="none"
    ONCONET_CONFIG = {}
    ONCODATA_CONFIG = {
        'convertor': 'dcmtk',
        'temp_img_dir': '/home/yala/OncoServe/tmp_images'
    }
    ONCONET_ARGS = Args(ONCONET_CONFIG)
    ONCODATA_ARGS = Args(ONCODATA_CONFIG)
    ONCOSERVE_VERSION = '0.2.0'
    ONCODATA_VERSION = '0.2.0'
    ONCONET_VERSION =  '0.2.0'
    ONCOQUERIES_VERSION = '0.2.0'
    NAME = 'BaseConfig'
    PORT = 5009


class MammoCancerMirai(Config):
    NAME = '2D_Mammo_Cancer_Mirai'
    AGGREGATION="max"

    ONCONET_CONFIG = {
        'cuda': False,
        'img_mean': [7047.99],
        'img_std': [12005.5],
        'img_size': [1664,2048],
        'num_chan': 3,
        'num_gpus': 1,
        'test_image_transformers': ['scale_2d', 'align_to_left'],
        'test_tensor_transformers': ["force_num_chan_2d", "normalize_2d"],
        'additional': None,
        'img_encoder_snapshot': 'model/snapshots/mgh_mammo_MIRAI_Base_May20_2019.p',
        'transformer_snapshot': 'model/snapshots/mgh_mammo_cancer_MIRAI_Transformer_Jan13_2020.p',
        'video':False,
        "pred_risk_factors": True,
        'use_pred_risk_factors_at_test': True,
        'pred_both_sides': False,
        'multi_image': True,
        'num_images': 4,
        'wrap_model':False,
        'state_dict_path': None,
        'snapshot': None,
        'min_num_images': 4,
        'model_name': 'mirai_full',
        'max_followup': 5,
        'use_risk_factors': True,
        "use_region_annotation": False,
        'risk_factor_keys': "density binary_family_history binary_biopsy_benign binary_biopsy_LCIS binary_biopsy_atypical_hyperplasia age menarche_age menopause_age first_pregnancy_age prior_hist race parous menopausal_status weight height ovarian_cancer ovarian_cancer_age ashkenazi brca mom_bc_cancer_history m_aunt_bc_cancer_history p_aunt_bc_cancer_history m_grandmother_bc_cancer_history p_grantmother_bc_cancer_history sister_bc_cancer_history mom_oc_cancer_history m_aunt_oc_cancer_history p_aunt_oc_cancer_history m_grandmother_oc_cancer_history p_grantmother_oc_cancer_history sister_oc_cancer_history hrt_type hrt_duration hrt_years_ago_stopped",
        'use_second_order_risk_factor_features': False,
        'callibrator_path': 'model/snapshots/callibrators/MIRAI_FULL_PRED_RF.callibrator.p'
    }
    ONCONET_ARGS = Args(ONCONET_CONFIG)