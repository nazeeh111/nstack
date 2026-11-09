"""Owned Blender5.2.1 rigid-body cache fixture; run --background --factory-startup.

Usage: blender ... --python THIS_FILE -- create|reopen ABSOLUTE_OUTPUT_DIR
Reopen uses the saved blend as input. It never opens or modifies other projects.
"""
import bpy,json,sys,pathlib
mode,raw=sys.argv[sys.argv.index('--')+1:];out=pathlib.Path(raw).resolve();out.mkdir(parents=True,exist_ok=True);sc=bpy.context.scene
if mode=='create':
 for ob in list(sc.objects):bpy.data.objects.remove(ob,do_unlink=True)
 sc.frame_start=1;sc.frame_end=48;sc.render.fps=24
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,3));box=bpy.context.object;box.name='OwnedFallingCube';bpy.ops.rigidbody.object_add();box.rigid_body.type='ACTIVE';box.rigid_body.collision_shape='BOX';box.rigid_body.restitution=0
 bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,-.25));floor=bpy.context.object;floor.name='OwnedFloor';floor.scale=(10,10,.5);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);bpy.ops.rigidbody.object_add();floor.rigid_body.type='PASSIVE';floor.rigid_body.collision_shape='BOX'
 bpy.ops.object.camera_add(location=(7,-9,6));camera=bpy.context.object;camera.rotation_euler=((__import__('mathutils').Vector((0,0,1))-camera.location).to_track_quat('-Z','Y').to_euler());sc.camera=camera
 bpy.ops.object.light_add(type='AREA',location=(0,-3,7));bpy.context.object.data.energy=1500;bpy.context.object.data.shape='DISK';bpy.context.object.data.size=5
 cache=sc.rigidbody_world.point_cache;cache.frame_start=1;cache.frame_end=48;cache.use_disk_cache=False
 with bpy.context.temp_override(point_cache=cache):bpy.ops.ptcache.bake(bake=True)
 assert cache.is_baked
 sc.frame_set(48);bpy.context.view_layer.update();z=box.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.z
 assert .45<z<.6,z
 bpy.ops.wm.save_as_mainfile(filepath=str(out/'rigidbody.blend'))
 (out/'create.json').write_text(json.dumps({'version':bpy.app.version_string,'system':'RigidBodyWorld/BOX','frames':[1,48],'fps':24,'baked':cache.is_baked,'disk_cache':False,'end_z':z,'assets':'procedural; no external dependencies','invalidation':'Changes to collider geometry, transforms, mass/world or frame range require freeing and rebaking cache; cloth/fluid/GN require their own cache acceptance.'},indent=2))
elif mode=='reopen':
 cache=sc.rigidbody_world.point_cache;assert cache.is_baked;box=bpy.data.objects['OwnedFallingCube'];samples=[]
 for f in (48,1,25):
  sc.frame_set(f);bpy.context.view_layer.update();z=box.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.translation.z
  assert (.45<z<.6 if f==48 else abs(z-3)<.01 if f==1 else .45<z<3), (f,z)
  samples.append({'frame':f,'z':z})
 sc.render.engine='CYCLES';sc.cycles.samples=8;sc.render.resolution_x=256;sc.render.resolution_y=192;sc.render.resolution_percentage=100
 sc.render.image_settings.file_format='PNG';sc.render.filepath=str(out/'simulation.png');bpy.ops.render.render(write_still=True)
 sc.render.image_settings.file_format='OPEN_EXR';sc.render.image_settings.color_depth='16';sc.render.filepath=str(out/'simulation.exr');bpy.ops.render.render(write_still=True)
 for name in ['simulation.png','simulation.exr']:
  im=bpy.data.images.load(str(out/name),check_existing=False);assert tuple(im.size)==(256,192);assert max(im.pixels[:])>.2
 (out/'reopen.json').write_text(json.dumps({'version':bpy.app.version_string,'baked_on_reopen':True,'random_frames':samples,'png_and_16bit_exr_decoded':True,'scope':'Only embedded rigidbody cache. Cloth/fluid/GN/other solvers remain task-specific.'},indent=2))
else:raise ValueError('create or reopen required')
