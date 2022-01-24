# IDE for SDF

This is an Interactive Design/Development Environment for [SDF](https://github.com/fogleman/sdf), or actually any alike mesh

The idea is while modifying a sdf script, one can see "live-change" in a seprated window.

Requirement.txt:

 * [pyrender](https://github.com/mmatl/pyrender)
 * [trimesh](https://github.com/mikedh/trimesh)
 * [numpy](https://github.com/numpy/numpy)
 

## Usage

    from sdfide import ide
    f = ...any sdf constructs...
    ide.showsdf(f)

## Demo

Execute demo.py, change the last line and watch live change on the viewer
