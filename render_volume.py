import vtk
from vtk.web import protocols, server
from vtk.web import wamp as vtk_wamp

try:
    import argparse
except ImportError:
    # since  Python 2.6 and earlier don't have argparse, we simply provide
    # the source for the same as _argparse and we use it instead.
    from vtk.util import _argparse as argparse
    


# =============================================================================
# Create custom File Opener class to handle clients requests
# =============================================================================

class _WebCone(vtk_wamp.ServerProtocol):

    # Application configuration
    view    = None
    authKey = "vtkweb-secret"
    
    def do_VTK(self):
        # VTK specific code
        renderer = vtk.vtkRenderer()
        renderWindow = vtk.vtkRenderWindow()
        renderWindow.AddRenderer(renderer)

        renderWindowInteractor = vtk.vtkRenderWindowInteractor()
        renderWindowInteractor.SetRenderWindow(renderWindow)
        renderWindowInteractor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
	
    	reader = vtk.vtkNrrdReader()
        reader.SetFileName('../volume/' + filename)
        reader.Update()
            
        surface_extractor = vtk.vtkMarchingCubes()
        surface_extractor.SetInputConnection(reader.GetOutputPort())
        surface_extractor.SetValue(0,350)
        surface_extractor.ComputeNormalsOn()
        surface_extractor.ComputeScalarsOn()
        surface_extractor.Update()
            
        mapper = vtk.vtkPolyDataMapper()
        actor = vtk.vtkActor()

        mapper.SetInputConnection(surface_extractor.GetOutputPort())
        mapper.ScalarVisibilityOff()
        actor.SetMapper(mapper)

        renderer.AddActor(actor)
        renderer.ResetCamera()
        renderWindow.Render()
        
        return renderWindow

    def initialize(self):
        global renderer, renderWindowInteractor, cone, mapper, actor

        # Bring used components
        self.registerVtkWebProtocol(protocols.vtkWebMouseHandler())
        self.registerVtkWebProtocol(protocols.vtkWebViewPort())
        self.registerVtkWebProtocol(protocols.vtkWebViewPortImageDelivery())
        self.registerVtkWebProtocol(protocols.vtkWebViewPortGeometryDelivery())

        # Create default pipeline (Only once for all the session)
        if not _WebCone.view:
            # VTK Web application specific
            renderWindow = self.do_VTK()
            _WebCone.view = renderWindow

            self.Application.GetObjectIdMap().SetActiveObject("VIEW", renderWindow)
            # self.Application.GetObjectIdMap().SetActiveObject("VIEW", renderWindow)

# =============================================================================
# Main: Parse args and start server
# =============================================================================

if __name__ == "__main__":
    # Create argument parser
    parser = argparse.ArgumentParser(description="VTK/Web web-application")

    parser.add_argument("--filename",
                        help="read filename from other request",
                        type=str, default='volume2.nrrd')
    # Add default arguments
    server.add_arguments(parser)

    global filename
    # Exctract arguments
    args = parser.parse_args()

    filename = args.filename
    # Configure our current application
    _WebCone.authKey = args.authKey

    # Start server
    server.start_webserver(options=args, protocol=_WebCone)
