package com.example.parkiqpolice;

public class DeploymentModel {

    private String id;
    private String hotspot;
    private String police_station;
    private String vehicle;
    private String status;

    private long officers_required;
    private long violations;
    private long timestamp;

    public DeploymentModel() {
    }

    public DeploymentModel(
            String id,
            String hotspot,
            String police_station,
            String vehicle,
            String status,
            long officers_required,
            long violations,
            long timestamp
    ) {
        this.id = id;
        this.hotspot = hotspot;
        this.police_station = police_station;
        this.vehicle = vehicle;
        this.status = status;
        this.officers_required = officers_required;
        this.violations = violations;
        this.timestamp = timestamp;
    }

    public String getId() {
        return id;
    }

    public String getHotspot() {
        return hotspot;
    }

    public String getPolice_station() {
        return police_station;
    }

    public String getVehicle() {
        return vehicle;
    }

    public String getStatus() {
        return status;
    }

    public long getOfficers_required() {
        return officers_required;
    }

    public long getViolations() {
        return violations;
    }

    public long getTimestamp() {
        return timestamp;
    }
}