import bpy
import math

class POSE_OT_AtoT(bpy.types.Operator):
    """Rotate from A to T pose"""
    bl_idname = "pose.rotate_atot"
    bl_label = "Rotate A to T"

    def execute(self, context):
        if context.active_object.type != 'ARMATURE':
            self.report({'ERROR'}, "Please select an armature.")
            return {'CANCELLED'}

        bone_rotations = {
            "Left shoulder": -10.7,
            "Right shoulder": 10.7,
            "Left arm": -29.54,
            "Right arm": 29.54,
        }

        bpy.ops.object.mode_set(mode='POSE')

        for bone_name, rotation_deg in bone_rotations.items():
            bone = context.active_object.pose.bones.get(bone_name)
            if bone:
                if bone.rotation_mode not in {'XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'}:
                    bone.rotation_mode = 'XYZ'
                bone.rotation_euler[2] += math.radians(rotation_deg)
            else:
                self.report({'ERROR'}, f"Bone '{bone_name}' not found.")

        context.view_layer.update()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Select the mesh that's connected to the armature
        armature = context.active_object
        mesh_obj = None
        for obj in armature.children:
            if obj.type == 'MESH':
                mesh_obj = obj
                break

        if not mesh_obj:
            self.report({'ERROR'}, "No mesh object found that is parented to the armature.")
            return {'CANCELLED'}

        # Copy all the shape keys to a temporary object
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
        temp_obj = bpy.context.active_object

        # Delete all the shape keys on the original mesh object
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.shape_key_clear()
        
        # Apply the armature modifier
        for modifier in mesh_obj.modifiers:
            if modifier.type == 'ARMATURE':
                bpy.ops.object.modifier_apply(modifier=modifier.name)

        # Change to pose mode and apply as rest pose
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='POSE')
        bpy.ops.pose.armature_apply()
        bpy.ops.object.mode_set(mode='OBJECT')

        # Ensure a Basis shape key is created for the mesh after applying the rest pose
        mesh_obj.shape_key_add(name="Basis", from_mix=False)

        # Iterate over all shape keys in the temporary object
        if temp_obj.data.shape_keys:
            key_blocks = temp_obj.data.shape_keys.key_blocks
            for key_name in key_blocks.keys():
                # Do not skip the 'Basis' shape key this time
                # Add a new shape key to the original mesh object for each shape key in the temp object
                original_shape_key = mesh_obj.shape_key_add(name=key_name, from_mix=False)
                original_shape_key.value = key_blocks[key_name].value

                # Copy the vertex positions from the temp object's shape key to the original object's new shape key
                for i, vert in enumerate(temp_obj.data.vertices):
                    original_shape_key.data[i].co = key_blocks[key_name].data[i].co

        # Delete the temporary object after copying all shape keys
        bpy.data.objects.remove(temp_obj, do_unlink=True)

        # Apply a new armature modifier with the previous armature as the object
        new_arm_mod = mesh_obj.modifiers.new(name="Armature", type='ARMATURE')
        new_arm_mod.object = armature
        bpy.context.view_layer.objects.active = armature

        return {'FINISHED'}
