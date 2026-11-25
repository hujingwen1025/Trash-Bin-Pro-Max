from pathlib import Path
import json
import vtk

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'Source/Illustrations'
WIDTH,HEIGHT=1600,1400
COLORS={'C01_curved_corner':(.18,.55,.60),'M01_magnet_insert':(.18,.55,.60),
        'W01_rear':(.76,.65,.51),'W02_right':(.74,.63,.49),'W03_front':(.86,.75,.61),
        'W04_left':(.82,.70,.56),'F01_floor':(.81,.69,.54)}
DATA={}
for name in COLORS:
    reader=vtk.vtkSTLReader();reader.SetFileName(str(ROOT/'Source/MasterGeometry'/f'{name}.stl'));reader.Update()
    normals=vtk.vtkPolyDataNormals();normals.SetInputConnection(reader.GetOutputPort());normals.SetFeatureAngle(35);normals.Update()
    DATA[name]=vtk.vtkPolyData();DATA[name].DeepCopy(normals.GetOutput())
ALL=['C01_curved_corner','W03_front','W04_left','W01_rear','W02_right','F01_floor']
INDEX={}

def render(name,parts,highlight=None,positions=None,focus=(175,175,220),camera=(-800,-850,780),scale=350,invert=False,anchors=None,arrows=None):
    positions=positions or {}
    ren=vtk.vtkRenderer();ren.SetBackground(1,1,1)
    win=vtk.vtkRenderWindow();win.SetOffScreenRendering(1);win.SetSize(WIDTH,HEIGHT);win.AddRenderer(ren);win.SetMultiSamples(8)
    def point(q):
        x,y,z=q
        return (x,352.5-y,450-z) if invert else (x,y,z)
    for part in parts:
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(DATA[part])
        actor=vtk.vtkActor();actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*((.94,.64,.20)if part==highlight else COLORS[part]))
        actor.GetProperty().SetAmbient(.3);actor.GetProperty().SetDiffuse(.7);actor.GetProperty().SetSpecular(.08)
        shift=positions.get(part,(0,0,0))
        transform=vtk.vtkTransform()
        if invert:
            transform.Translate(0,352.5,450);transform.Scale(1,-1,-1)
        transform.Translate(*shift)
        actor.SetUserTransform(transform)
        ren.AddActor(actor)
    cam=ren.GetActiveCamera();cam.SetPosition(*camera);cam.SetFocalPoint(*focus);cam.SetViewUp(0,0,1);cam.ParallelProjectionOn();cam.SetParallelScale(scale)
    ren.ResetCameraClippingRange();win.Render()
    def project(q):
        ren.SetWorldPoint(*point(q),1);ren.WorldToDisplay();xx,yy,_=ren.GetDisplayPoint()
        return [xx,HEIGHT-yy]
    INDEX[name]={'width':WIDTH,'height':HEIGHT,'anchors':{k:project(v)for k,v in (anchors or {}).items()},
                 'arrows':[[project(a),project(b)]for a,b in (arrows or [])]}
    image=vtk.vtkWindowToImageFilter();image.SetInput(win);image.ReadFrontBufferOff();image.Update()
    writer=vtk.vtkPNGWriter();writer.SetFileName(str(OUT/f'{name}.png'));writer.SetInputConnection(image.GetOutputPort());writer.Write();win.Finalize()
    print('Rendered',name,flush=True)

render('overview',ALL,anchors={'C01':(53,53,280),'W03':(240,5.5,300),'W04':(5.5,240,300),'W01':(180,347,450),'W02':(347,180,450)})
render('exploded',ALL,positions={'W03_front':(0,-55,0),'W04_left':(-55,0,0),'W01_rear':(0,55,0),'W02_right':(55,0,0),'C01_curved_corner':(-30,-30,0),'F01_floor':(0,0,-55)},scale=395)
render('curve_inside',['C01_curved_corner'],focus=(65,65,225),camera=(650,700,610),scale=285,
       anchors={'M3':(120.5,13.5,225),'M4':(70.711,70.711,17),'UP':(75,75,450)})
render('curve_print',['C01_curved_corner'],focus=(65,65,225),camera=(650,700,650),scale=285,
       anchors={'BASE':(53,53,0),'PADS':(70.711,70.711,13),'FINGERS':(105,5.5,260),'NUTS':(120.5,13.5,225)},arrows=[((145,145,30),(145,145,430))])
render('stage_front',['C01_curved_corner','W03_front'],highlight='W03_front',positions={'W03_front':(60,0,0)},scale=360,
       anchors={'C01':(53,53,300),'W03':(275,5.5,315)},arrows=[((260,5.5,375),(200,5.5,375))])
render('stage_left',['C01_curved_corner','W03_front','W04_left'],highlight='W04_left',positions={'W04_left':(0,60,0)},scale=370,
       anchors={'W04':(5.5,280,315),'W03':(240,5.5,300)},arrows=[((5.5,260,375),(5.5,200,375))])
render('stage_rear',['C01_curved_corner','W03_front','W04_left','W01_rear'],highlight='W01_rear',positions={'W01_rear':(0,60,0)},scale=380,
       anchors={'W01':(185,407,450)},arrows=[((185,407,480),(185,347,480))])
render('stage_right',ALL[:-1],highlight='W02_right',positions={'W02_right':(60,0,0)},scale=380,
       anchors={'W02':(407,185,450)},arrows=[((407,185,480),(347,185,480))])
render('stage_floor',ALL,highlight='F01_floor',positions={'F01_floor':(0,0,-55)},invert=True,scale=385,
       anchors={'F01':(175,175,-55),'RIM':(175,347,450)},arrows=[((175,175,-50),(175,175,-6))])
render('print_joint',['C01_curved_corner','W03_front'],highlight='W03_front',focus=(102.5,5.5,225),camera=(140,-480,310),scale=43)
render('wood_joint',['W01_rear','W04_left'],highlight='W01_rear',focus=(5.5,347,225),camera=(-300,650,320),scale=45)
render('floor_joint',['W03_front','F01_floor'],highlight='F01_floor',focus=(145.5,5.5,8),camera=(180,-250,135),scale=37)
render('m3_pocket',['C01_curved_corner'],focus=(120.5,13.5,225),camera=(145,250,270),scale=14,
       anchors={'TRAP':(120.5,13.5,225)})
render('m4_pad',['C01_curved_corner'],focus=(70.711,70.711,13),camera=(160,175,165),scale=23,
       anchors={'TRAP':(70.711,70.711,17)})
render('floor_bottom',['F01_floor'],focus=(176,176,5),camera=(176,-100,-900),scale=245,
       anchors={'M4':(70.711,70.711,0),'M01':(102.5,102.5,0)})
render('front_outside',['W03_front'],focus=(223,5.5,225),camera=(223,-900,330),scale=270,
       anchors={'CS':(120.5,2.5,225)})
# M01 is shown in installed orientation and in the inverted print orientation.
render('insert_installed',['M01_magnet_insert'],focus=(0,0,4),camera=(45,-55,-45),scale=23)
# Turning the actor about X and translating up nine makes its closed roof the bed face.
actor_data=DATA['M01_magnet_insert'];rot=vtk.vtkTransform();rot.Translate(0,0,9);rot.RotateX(180)
f=vtk.vtkTransformPolyDataFilter();f.SetTransform(rot);f.SetInputData(actor_data);f.Update()
DATA['M01_magnet_insert']=f.GetOutput()
render('insert_print',['M01_magnet_insert'],focus=(0,0,4),camera=(45,-55,48),scale=23)
DATA['M01_magnet_insert']=actor_data
(OUT/'index.json').write_text(json.dumps(INDEX,indent=2))
