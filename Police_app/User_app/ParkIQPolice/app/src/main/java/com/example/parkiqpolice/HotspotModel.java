package com.example.parkiqpolice;

public class HotspotModel {

    private String junctionName;
    private String policeStation;
    private String priorityLevel;
    private double priorityScore;
    private long violations;
    private String peakHour;
    private long rank;

    private double latitude;
    private double longitude;

    public HotspotModel() {
    }

    public HotspotModel(
            String junctionName,
            String policeStation,
            String priorityLevel,
            double priorityScore,
            long violations,
            String peakHour,
            long rank,
            double latitude,
            double longitude
    ) {
        this.junctionName = junctionName;
        this.policeStation = policeStation;
        this.priorityLevel = priorityLevel;
        this.priorityScore = priorityScore;
        this.violations = violations;
        this.peakHour = peakHour;
        this.rank = rank;
        this.latitude = latitude;
        this.longitude = longitude;
    }

    public String getJunctionName() {
        return junctionName;
    }

    public String getPoliceStation() {
        return policeStation;
    }

    public String getPriorityLevel() {
        return priorityLevel;
    }

    public double getPriorityScore() {
        return priorityScore;
    }

    public long getViolations() {
        return violations;
    }

    public String getPeakHour() {
        return peakHour;
    }

    public long getRank() {
        return rank;
    }

    public double getLatitude() {
        return latitude;
    }

    public double getLongitude() {
        return longitude;
    }
}