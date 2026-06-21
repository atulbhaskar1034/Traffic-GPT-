package com.example.parkiqpolice;

import com.google.firebase.Timestamp;
import com.google.firebase.firestore.Exclude;
import com.google.firebase.firestore.PropertyName;

public class CommunityModel {

    private String type;
    private String location;
    private String status;
    private String vehicleType;

    private double latitude;
    private double longitude;

    private long scoreAwarded;

    @Exclude
    private long timestamp;

    public CommunityModel() {
    }

    public String getType() {
        return type;
    }

    public String getLocation() {
        return location;
    }

    public String getStatus() {
        return status;
    }

    public String getVehicleType() {
        return vehicleType;
    }

    public double getLatitude() {
        return latitude;
    }

    public double getLongitude() {
        return longitude;
    }

    public long getScoreAwarded() {
        return scoreAwarded;
    }

    @PropertyName("timestamp")
    public void setTimestamp(Object ts) {
        if (ts instanceof Timestamp) {
            this.timestamp = ((Timestamp) ts).toDate().getTime();
        } else if (ts instanceof Number) {
            this.timestamp = ((Number) ts).longValue();
        }
    }

    @Exclude
    public long getTimestamp() {
        return timestamp;
    }

    @Exclude
    public void setTimestamp(long timestamp) {
        this.timestamp = timestamp;
    }
}