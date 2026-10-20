import bpy, json
engines = [item.identifier for item in bpy.context.scene.render.bl_rna.properties['engine'].enum_items]
eevee = next((name for name in ('BLENDER_EEVEE_NEXT', 'BLENDER_EEVEE') if name in engines), None)
print('EEVEE_ENGINE_PROBE=' + json.dumps({'available': eevee is not None, 'selected': eevee, 'engines': engines}))
if eevee is None:
    raise RuntimeError('No EEVEE engine is exposed by this Blender build')
