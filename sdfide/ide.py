# ----------------------------------------------------------------------------
# sdfide
# Copyright (c) 2022- juju2013@github
# All rights reserved.
#
# This file is under BSD 2-Clause License, see LICENSE file
#
# ----------------------------------------------------------------------------

"""Interactive Design Environment for SDF

This module provides a simple mesh viewer with pyrender (https://github.com/mmatl/pyrender)
with some additional features:
  * View a SDF (https://github.com/fogleman/sdf) object
  * Remember viewer position
  * Auto-refresh when calling script (or any other file) changed
"""

import __main__
import os, sys, logging, traceback
from configparser import ConfigParser
from threading import Thread
import pyrender
import numpy as np
import trimesh
from datetime import datetime
import time

log = logging.getLogger("SdfIDE")
config = ConfigParser()
CFG=".sdf.ini"

def INFO(*args):
  log.info(args)
  
def WARN(*args):
  log.warn(args)
  
def ERROR(*args):
  log.error(args)
  
def DEBUG(*args):
  log.debug(args)
  

class CustomViewer(pyrender.Viewer):
  """Customized viewer which remember its size"""
  
  def on_close(self):
    """Memorize viewer position before close"""
    
    self.x, self.y = self.get_location()
    super(CustomViewer, self).on_close()
    

class IDE():
  """Mesh viewer with pyrender
  
  * Remember window position
  * Refresh when main scipt changed
  """

  def __init__(self):
    """Initialize internal states and start viewer/autoreload threads
    """
    self.viewer = None
    self.node = None
    self.watchers = {}
    self._main = None

    config.read(CFG)
    h = logging.StreamHandler(sys.stdout)
    f = logging.Formatter('%(asctime)s:%(name)s:%(levelname)s:%(message)s')
    log.setLevel(config.getint("debug", "loglevel", fallback=20))
    h.setFormatter(f)
    log.addHandler(h)
    INFO("sdfide initializing...")
    tm = Thread(target=self.run)
    tm.start()
    Thread(target=self.watch).start()
  
  def run(self):
    """Initialize the viewer"""
    
    if hasattr(__main__, "__file__"):
      self._main = os.path.abspath(sys.modules['__main__'].__file__)
      self.watchfile(self._main)
    scene = pyrender.Scene()
    x=config.getint("main", "x", fallback=10)
    y=config.getint("main", "y", fallback=10)
    w=config.getint("main", "w", fallback=600)
    h=config.getint("main", "h", fallback=600)
    self.viewer=CustomViewer(scene, use_raymond_lighting=True, run_in_thread=True, show_world_axis=True, window_title=self._main, viewport_size=(w,h))
    self.viewer.x = x
    self.viewer.x = y
    
    # XXX FIXME : how to properly position the window ?
    time.sleep(0.5)
    while self.viewer._window is None:
      time.sleep(0.2)
    self.viewer.set_location(x,y)
    
    INFO("sdfide ready")
    
  def show(self, pts):
    """Display the mesh
    
    Args:
      pts: a numpy array (,3) of vertice forming the mesh object
    """
    DEBUG("Showing ", type(pts))

    ts = datetime.now()
    faces = np.arange((len(pts)//3) * 3).reshape((-1,3))
    tm = trimesh.Trimesh(vertices=pts,faces=faces, process=True)
    mesh = pyrender.Mesh.from_trimesh(tm)
    te = datetime.now()
    td = te - ts
    INFO("Rendered in %s.%s seconds"%(td.seconds, td.microseconds))
    if self.viewer:
      self.viewer.render_lock.acquire()
      if self.node:
        self.viewer.scene.remove_node(self.node)
        self.node = None
      self.node = self.viewer.scene.add(mesh)
      self.viewer.render_lock.release()
    else:
      ERROR("Viewer not initialized")

  def savestate(self):
    """Save the viewer position"""
    
    # default size
    x=y=10
    w=h=600
    try :
      w,h=self.viewer.viewport_size
      x,y=(self.viewer.x, self.viewer.y)
    except:
      pass
    try:
      config.add_section("main")
    except:
      pass
    config.set("main", "x", f"{x}")
    config.set("main", "y", f"{y}")
    config.set("main", "w", f"{w}")
    config.set("main", "h", f"{h}")
    with open(CFG, "w") as cfg:
      config.write(cfg)

  def watchfile(self, wf):
    """Add a file to watch list for autoreload"""
    try:
      self.watchers[wf] = os.stat(wf)
      DEBUG("Now watching file ", wf)
    except:
      DEBUG("Cannot stat file ", wf)
    
  def watch(self):
    """Thread to watch file changes"""
    
    time.sleep(2)
    while self.viewer.is_active :
      for f, ost in self.watchers.items() :
        nst = os.stat(f)
        # only reload if file is stalled for more than 1 second
        if nst.st_mtime - ost.st_mtime > 1:
          self.watchers[f]=nst
          DEBUG("Reload %s"%f)
          # we always reload the main script as we've no clue about dependencies
          self.reload_main()
          break
      time.sleep(1)
    DEBUG("Watcher quit")
    self.savestate()

  def reload_main(self):
    """Relaod the __main__ script"""
    
    import importlib.machinery as im
    import importlib.util as iu
    try:
      """Load and execute the main script as module but don't put it in cache"""
      loader = im.SourceFileLoader('_main', self._main)
      spec = iu.spec_from_loader('_main', loader)
      module = iu.module_from_spec(spec)
      loader.exec_module(module)
    except:
      print(traceback.format_exc())
    
ide = IDE()

def showsdf(obj):
  """show a SDF object"""
  ide.show(obj.generate(verbose=False))
    
