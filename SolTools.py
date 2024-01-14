bl_info = {
    "name": "NFT Metadata Generator",
    "blender": (4, 0, 0),
    "category": "Object",
    "location": "View3D > Tool",
    "author": "Howie Sir",
    "description": "Generate NFT metadata and mint NFT using Helius API.",
    "version": (1, 0),
    "blender": (4, 0, 0),
    "wiki_url": "",
    "tracker_url": "",
}

import bpy
import os
import json
import requests

class HeliusAddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    api_key: bpy.props.StringProperty(name="API Key", description="Enter your Helius API Key", default="", subtype="PASSWORD")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        layout.label(text="Helius API Key:")
        row.prop(self, "api_key")

class Attr(bpy.types.PropertyGroup):
    trait_type: bpy.props.StringProperty(name="Trait Type")
    value: bpy.props.StringProperty(name="Value")

class File(bpy.types.PropertyGroup):
    uri: bpy.props.StringProperty(name="URI")
    typ: bpy.props.StringProperty(name="Type")
    cdn: bpy.props.BoolProperty(name="CDN")

class Creator(bpy.types.PropertyGroup):
    address: bpy.props.StringProperty(name="Address")
    share: bpy.props.FloatProperty(name="Share")

class OBJ_OT_AddAttr(bpy.types.Operator):
    bl_idname = "scene.add_attr"
    bl_label = "Add Attribute"
    def execute(self, context):
        context.scene.attrs.add()
        return {'FINISHED'}

class OBJ_OT_AddFile(bpy.types.Operator):
    bl_idname = "scene.add_file"
    bl_label = "Add File"
    def execute(self, context):
        context.scene.files.add()
        return {'FINISHED'}

class OBJ_OT_AddCreator(bpy.types.Operator):
    bl_idname = "scene.add_creator"
    bl_label = "Add Creator"
    def execute(self, context):
        context.scene.creator.add()
        return {'FINISHED'}

class OBJ_OT_GenerateMetadata(bpy.types.Operator):
    bl_idname = "object.generate_metadata"
    bl_label = "Generate Metadata"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    def execute(self, context):
        meta = {}
        for key in ["name", "symbol", "description", "image", "animation_url", "external_url", "category"]:
            value = getattr(context.scene, key)
            if value:
                meta[key] = value
        attrs = [{"trait_type": a.trait_type, "value": a.value} for a in context.scene.attrs if a.trait_type and a.value]
        files = [{"uri": f.uri, "type": f.typ, "cdn": f.cdn} for f in context.scene.files if f.uri and f.typ]
        if attrs:
            meta["attributes"] = attrs
        if files:
            meta["properties"] = {"files": files, "category": context.scene.category}
        output_file_name = context.scene.output_file_name
        blend_file_path = bpy.data.filepath
        blend_file_name = bpy.path.display_name_from_filepath(blend_file_path)
        output_file_path = os.path.join(os.path.dirname(blend_file_path), f"{output_file_name}.json")
        with open(output_file_path, 'w') as output_file:
            output_file.write(str(meta))
        return {'FINISHED'}

class OBJ_OT_MintNft(bpy.types.Operator):
    bl_idname = "object.mint_nft"
    bl_label = "Mint NFT"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__].preferences
        api_key = preferences.api_key

        if not api_key:
            self.report({'ERROR'}, "Helius API key is not set. Please set it in the addon preferences.")
            return {'CANCELLED'}
        url = f"https://mainnet.helius-rpc.com/?api-key={api_key}"
        data = {
            "jsonrpc": "2.0",
            "id": context.scene.name,
            "method": "mintCompressedNft",
            "params": {
                "name": context.scene.name,
                "symbol": context.scene.symbol,
                "owner": context.scene.mint_owner,
                "description": context.scene.description,
                "attributes": [
                    {"trait_type": a.trait_type, "value": a.value} for a in context.scene.attrs if a.trait_type and a.value
                ],
                "imageUrl": context.scene.image,
                "externalUrl": context.scene.external_url,
                "sellerFeeBasisPoints": context.scene.sellerFeeBasisPoints,
            },
        }
        response = requests.post(url, json=data)
        result = response.json().get('result')
        if result:
            print('Minted asset:', result.get('assetId'))
            self.report({'INFO'}, f"Minted asset: {result.get('assetId')}")
        else:
            self.report({'ERROR'}, "Failed to mint asset. Check the console for details.")
        return {'FINISHED'}

class MetPan(bpy.types.Panel):
    bl_label = "SOL Metadata Generator"
    bl_idname = "PT_MetPan"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        lay = self.layout
        main_panel = lay.column(align=True)
        main_panel.label(text="Metadata Generator:")
        metagen_subpanel = main_panel.box().column(align=True)
        row = metagen_subpanel.row(align=True)
        row.prop(context.scene, "name", text="Name")
        row.prop(context.scene, "symbol", text="Symbol")
        row = metagen_subpanel.row(align=True)
        row.prop(context.scene, "description", text="Description")
        row = metagen_subpanel.row(align=True)
        row.prop(context.scene, "image", text="Image Path")
        row = metagen_subpanel.row(align=True)
        row.prop(context.scene, "animation_url", text="Animation URL")
        row = metagen_subpanel.row(align=True)
        row.prop(context.scene, "external_url", text="External URL")
        row = metagen_subpanel.row(align=True)
        row.operator("scene.add_attr", text="", icon= 'PLUS')
        row.label(text="     Attributes:")
        for attr in context.scene.attrs:
            row = metagen_subpanel.row(align=True)
            row.prop(attr, "trait_type", text="Trait")
            row.prop(attr, "value", text="Value")
        row = metagen_subpanel.row(align=True)
        row.label(text="")
        row = metagen_subpanel.row(align=True)
        row.label(text="Properties:")
        row = metagen_subpanel.row(align=True)
        row.operator("scene.add_file", text="", icon= 'PLUS')
        row.label(text="     Files:")
        for file in context.scene.files:
            row = metagen_subpanel.row(align=True)
            row.prop(file, "uri", text="URI")
            row.prop(file, "typ", text="Type")
            row.prop(file, "cdn", text="CDN")
        metagen_subpanel.prop(context.scene, "category", text="Category")
        metagen_subpanel.prop(context.scene, "output_file_name", text="Output File Name")
        metagen_subpanel.operator("object.generate_metadata", text="Generate Metadata", icon='EXPORT')
        main_panel.label(text="Mint:")
        mint_subpanel = main_panel.box().column(align=True)
        row = mint_subpanel.row(align=True)
        row.prop(context.scene, "mint_owner", text="Mint Owner")
        row = mint_subpanel.row(align=True)
        row.prop(context.scene, "delegate", text="Delegate")
        row = mint_subpanel.row(align=True)
        row.prop(context.scene, "col", text="Collection")
        row.prop(context.scene, "sellerFeeBasisPoints", text="Seller Fee")
        row = mint_subpanel.row(align=True)
        row.operator("scene.add_creator", text="", icon= 'PLUS')
        row.label(text="Creators:")
        for creator in context.scene.creator:
            row = mint_subpanel.row(align=True)
            row.prop(creator, "address", text="Address")
            row.prop(creator, "share", text="Share")
        row = mint_subpanel.row(align=True)
        row.operator("object.mint_nft", text="Mint with Helius", icon='EXPORT')


classes = (MetPan, OBJ_OT_GenerateMetadata, OBJ_OT_AddAttr, OBJ_OT_AddFile, OBJ_OT_AddCreator, OBJ_OT_MintNft, Attr, File, Creator, HeliusAddonPreferences)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.Scene.name = bpy.props.StringProperty(name="Name")
    bpy.types.Scene.output_file_name = bpy.props.StringProperty(name="Output File Name")
    bpy.types.Scene.symbol = bpy.props.StringProperty(name="Symbol")
    bpy.types.Scene.description = bpy.props.StringProperty(name="Description")
    bpy.types.Scene.image = bpy.props.StringProperty(name="Image Path")
    bpy.types.Scene.animation_url = bpy.props.StringProperty(name="Animation URL")
    bpy.types.Scene.external_url = bpy.props.StringProperty(name="External URL")
    bpy.types.Scene.category = bpy.props.StringProperty(name="Category")
    bpy.types.Scene.sellerFeeBasisPoints = bpy.props.FloatProperty(name="sellerFeeBasisPoints")
    bpy.types.Scene.mint_owner = bpy.props.StringProperty(name="Mint Owner")
    bpy.types.Scene.delegate = bpy.props.StringProperty(name="Delegate")
    bpy.types.Scene.col = bpy.props.StringProperty(name="Collection")
    bpy.types.Scene.attrs = bpy.props.CollectionProperty(type=Attr)
    bpy.types.Scene.files = bpy.props.CollectionProperty(type=File)
    bpy.types.Scene.creator = bpy.props.CollectionProperty(type=Creator)


def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    del bpy.types.Scene.name
    del bpy.types.Scene.output_file_name
    del bpy.types.Scene.symbol
    del bpy.types.Scene.description
    del bpy.types.Scene.image
    del bpy.types.Scene.animation_url
    del bpy.types.Scene.external_url
    del bpy.types.Scene.category
    del bpy.types.Scene.attrs
    del bpy.types.Scene.files
    del bpy.types.Scene.sellerFeeBasisPoints
    del bpy.types.Scene.mint_owner
    del bpy.types.Scene.delegate
    del bpy.types.Scene.col
    del bpy.types.Scene.creator

if __name__ == "__main__":
    register()
