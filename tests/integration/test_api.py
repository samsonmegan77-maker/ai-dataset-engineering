def test_api_module_imports():
 from dataset_api.main import app
 assert any(route.path=='/health' for route in app.routes)
