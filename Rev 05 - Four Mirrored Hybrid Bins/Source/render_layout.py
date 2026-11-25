from pathlib import Path
import vtk,json
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'Source/Illustrations'
INDEX=json.loads((OUT/'index.json').read_text());W,H=1600,1400
for name,top in [('four_layout',False),('four_top',True)]:
 ren=vtk.vtkRenderer();ren.SetBackground(1,1,1);win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(W,H);win.SetMultiSamples(8);win.AddRenderer(ren)
 for b in ['B1','B2','B3','B4']:
  for part in ['W01','W02','W03','W04','F01','C01']:
   read=vtk.vtkSTLReader();read.SetFileName(str(ROOT/'STL'/f'{b}_{part}.stl'));read.Update();n=vtk.vtkPolyDataNormals();n.SetInputConnection(read.GetOutputPort());n.SetFeatureAngle(35);n.Update();m=vtk.vtkPolyDataMapper();m.SetInputConnection(n.GetOutputPort());a=vtk.vtkActor();a.SetMapper(m);a.GetProperty().SetColor(*((.18,.55,.60)if part=='C01'else(.83,.72,.57)));a.GetProperty().SetAmbient(.3);a.GetProperty().SetDiffuse(.7);ren.AddActor(a)
 cam=ren.GetActiveCamera();cam.SetPosition(*((0,0,1800)if top else(-1200,-1600,1400)));cam.SetFocalPoint(*((0,0,0)if top else(0,0,210)));cam.SetViewUp(*((0,1,0)if top else(0,0,1)));cam.ParallelProjectionOn();cam.SetParallelScale(420 if top else 650);ren.ResetCameraClippingRange();win.Render()
 def project(q):ren.SetWorldPoint(*q,1);ren.WorldToDisplay();x,y,_=ren.GetDisplayPoint();return[x,H-y]
 anchors={b:project((sx*220,sy*220,450 if not top else 9))for b,(sx,sy)in {'B1':(1,1),'B2':(-1,1),'B3':(1,-1),'B4':(-1,-1)}.items()}
 INDEX[name]={'width':W,'height':H,'anchors':anchors,'arrows':[]}
 im=vtk.vtkWindowToImageFilter();im.SetInput(win);im.ReadFrontBufferOff();im.Update();wr=vtk.vtkPNGWriter();wr.SetFileName(str(OUT/f'{name}.png'));wr.SetInputConnection(im.GetOutputPort());wr.Write();win.Finalize()
(OUT/'index.json').write_text(json.dumps(INDEX,indent=2))
