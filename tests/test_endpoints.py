import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Verify GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Should contain all 9 activities
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Science Club" in data

    def test_get_activities_returns_correct_structure(self, client):
        """Verify each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_get_activities_includes_initial_participants(self, client):
        """Verify activities include their initial participants"""
        response = client.get("/activities")
        data = response.json()
        
        assert "Chess Club" in data
        assert len(data["Chess Club"]["participants"]) == 2
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Verify user can successfully sign up for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Chess Club"

    def test_signup_adds_participant(self, client):
        """Verify signup actually adds the participant to the activity"""
        email = "testuser@mergington.edu"
        
        # Verify user not already in activity
        activities_before = client.get("/activities").json()
        assert email not in activities_before["Chess Club"]["participants"]
        
        # Sign up user
        client.post(f"/activities/Chess%20Club/signup?email={email}")
        
        # Verify user was added
        activities_after = client.get("/activities").json()
        assert email in activities_after["Chess Club"]["participants"]

    def test_signup_duplicate_rejected(self, client):
        """Verify user cannot sign up twice for same activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"

    def test_signup_nonexistent_activity(self, client):
        """Verify signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    @pytest.mark.parametrize("activity_name", [
        "Chess Club",
        "Programming Class",
        "Gym Class",
        "Basketball Team"
    ])
    def test_signup_multiple_activities(self, client, activity_name):
        """Verify signup works for multiple different activities"""
        email = "multistudent@mergington.edu"
        encoded_name = activity_name.replace(" ", "%20")
        
        response = client.post(
            f"/activities/{encoded_name}/signup?email={email}"
        )
        assert response.status_code == 200

    def test_signup_special_characters_in_email(self, client):
        """Verify signup works with valid special characters in email"""
        email = "john.doe+test@mergington.edu"
        response = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Verify user can successfully unregister from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Removed michael@mergington.edu from Chess Club"

    def test_unregister_removes_participant(self, client):
        """Verify unregister actually removes the participant"""
        email = "michael@mergington.edu"
        
        # Verify user exists in activity
        activities_before = client.get("/activities").json()
        assert email in activities_before["Chess Club"]["participants"]
        count_before = len(activities_before["Chess Club"]["participants"])
        
        # Unregister user
        client.delete(f"/activities/Chess%20Club/unregister?email={email}")
        
        # Verify user was removed and count decreased
        activities_after = client.get("/activities").json()
        assert email not in activities_after["Chess Club"]["participants"]
        assert len(activities_after["Chess Club"]["participants"]) == count_before - 1

    def test_unregister_not_signed_up(self, client):
        """Verify unregister fails if user not signed up"""
        email = "nosignup@mergington.edu"
        
        response = client.delete(
            f"/activities/Chess%20Club/unregister?email={email}"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not signed up for this activity"

    def test_unregister_nonexistent_activity(self, client):
        """Verify unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_then_resign_up(self, client):
        """Verify user can sign up again after unregistering"""
        email = "testuser2@mergington.edu"
        activity = "Soccer%20Club"
        
        # Sign up
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Sign up again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_index(self, client):
        """Verify GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"

    def test_root_with_follow_redirects(self, client):
        """Verify root can be accessed with redirect following"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
