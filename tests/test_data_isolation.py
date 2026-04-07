import pytest
from fastapi.testclient import TestClient


class TestDataIsolation:
    """Tests to verify activity data isolation between test runs"""

    def test_multiple_signups_independent(self, client):
        """Verify signups in one test don't affect another test's state"""
        # Sign up first user
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=isolation1@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Verify participant count
        activities1 = client.get("/activities").json()
        count1 = len(activities1["Chess Club"]["participants"])
        
        # This count should persist only within this test
        assert "isolation1@mergington.edu" in activities1["Chess Club"]["participants"]
        assert count1 >= 3  # Original 2 + new signup

    def test_unregister_isolation(self, client):
        """Verify unregisters in one test start fresh in each test"""
        # Get initial participants
        activities_initial = client.get("/activities").json()
        initial_count = len(activities_initial["Chess Club"]["participants"])
        
        # Should have original participants
        assert "michael@mergington.edu" in activities_initial["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in activities_initial["Chess Club"]["participants"]

    def test_signup_and_unregister_sequence(self, client):
        """Verify signup followed by unregister works within test isolation"""
        email = "sequence@mergington.edu"
        activity = "Programming%20Class"
        
        # Sign up
        client.post(f"/activities/{activity}/signup?email={email}")
        activities_after_signup = client.get("/activities").json()
        assert email in activities_after_signup["Programming Class"]["participants"]
        count_after_signup = len(activities_after_signup["Programming Class"]["participants"])
        
        # Unregister
        client.delete(f"/activities/{activity}/unregister?email={email}")
        activities_after_unregister = client.get("/activities").json()
        assert email not in activities_after_unregister["Programming Class"]["participants"]
        count_after_unregister = len(activities_after_unregister["Programming Class"]["participants"])
        
        # Count should decrease
        assert count_after_unregister == count_after_signup - 1

    def test_independent_activity_modifications(self, client):
        """Verify modifications to one activity don't affect others"""
        # Sign up to Chess Club
        client.post("/activities/Chess%20Club/signup?email=activity1@mergington.edu")
        
        activities = client.get("/activities").json()
        chess_participants = len(activities["Chess Club"]["participants"])
        soccer_participants = len(activities["Soccer Club"]["participants"])
        
        # Verify only Chess Club was modified
        assert "activity1@mergington.edu" in activities["Chess Club"]["participants"]
        assert "activity1@mergington.edu" not in activities["Soccer Club"]["participants"]

    def test_fresh_state_for_each_test(self, client):
        """Verify each test class gets fresh app state"""
        # Check original participants count
        activities = client.get("/activities").json()
        
        # These should be the original counts from conftest
        assert len(activities["Chess Club"]["participants"]) == 2
        assert len(activities["Programming Class"]["participants"]) == 2
        assert len(activities["Basketball Team"]["participants"]) == 1
        assert len(activities["Soccer Club"]["participants"]) == 2
