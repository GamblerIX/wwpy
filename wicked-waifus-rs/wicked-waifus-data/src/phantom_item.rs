use serde::Deserialize;

#[derive(Deserialize)]
#[serde(rename_all = "PascalCase")]
pub struct MainProp {
    pub rand_group_id: i32,
    pub rand_num: i32,
}

#[derive(Deserialize)]
#[cfg_attr(feature = "strict_json_fields", serde(deny_unknown_fields))]
#[serde(rename_all = "PascalCase")]
pub struct PhantomItemData {
    pub item_id: i32,
    pub monster_id: i32,
    #[cfg(feature = "strict_json_fields")]
    pub monster_name: String,
    pub element_type: Vec<i32>,
    pub main_prop: MainProp,
    pub level_up_group_id: i32,
    pub skill_id: i32,
    pub calabash_buffs: Vec<i32>,
    pub rarity: i32,
    pub mesh_id: i32,
    pub zoom: [f32; 3],
    pub location: [f32; 3],
    pub rotator: [f32; 3],
    #[cfg(feature = "strict_json_fields")]
    pub stand_anim: String,
    #[cfg(feature = "strict_json_fields")]
    pub type_description: String,
    #[cfg(feature = "strict_json_fields")]
    pub attributes_description: String,
    #[cfg(feature = "strict_json_fields")]
    pub icon: String,
    #[cfg(feature = "strict_json_fields")]
    pub icon_middle: String,
    #[cfg(feature = "strict_json_fields")]
    pub icon_small: String,
    #[cfg(feature = "strict_json_fields")]
    pub mesh: String,
    pub quality_id: i32,
    pub max_capcity: i32,
    pub item_access: Vec<i32>,
    pub obtained_show: i32,
    #[cfg(feature = "strict_json_fields")]
    pub obtained_show_description: String,
    pub num_limit: i32,
    pub show_in_bag: bool,
    pub sort_index: i32,
    #[cfg(feature = "strict_json_fields")]
    pub skill_icon: String,
    pub destructible: bool,
    pub red_dot_disable_rule: i32,
    pub fetter_group: Vec<i32>,
    pub phantom_type: i32,
    pub parent_monster_id: i32,
}