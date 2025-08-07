use serde::Deserialize;

#[derive(Debug, Deserialize)]
#[cfg_attr(feature = "strict_json_fields", serde(deny_unknown_fields))]
#[serde(rename_all = "PascalCase")]
pub struct SummonCfgData {
    pub id: i32,
    pub blueprint_type: String,
    #[cfg(feature = "strict_json_fields")]
    pub name: String,
    pub born_buff_id: Vec<i64>,
}