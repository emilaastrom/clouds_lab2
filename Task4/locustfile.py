from locust import HttpUser, task, between

class IntegrationUser(HttpUser):
    
    @task
    def test_integration(self):
        self.client.get("/numericalintegral/0.0/3.14159")