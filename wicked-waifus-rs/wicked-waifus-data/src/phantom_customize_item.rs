use serde::Deserialize;

#[derive(Deserialize)]
#[cfg_attr(feature = "strict_json_fields", serde(deny_unknown_fields))]
#[serde(rename_all = "PascalCase")]
pub struct PhantomCustomizeItemData {
    pub item_id: i32,
    pub phantom_id: i32,
    pub skin_item_id: i32,
}