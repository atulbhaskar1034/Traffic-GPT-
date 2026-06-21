package com.example.parkiqpolice;

import android.Manifest;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.gms.location.FusedLocationProviderClient;
import com.google.android.gms.location.LocationServices;
import com.google.firebase.firestore.FirebaseFirestore;

import java.io.IOException;
import java.util.List;
import java.util.Locale;

public class DashboardActivity extends BaseNavigationActivity {

    @Override
    protected int getContentLayoutId() {
        return R.layout.activity_dashboard;
    }

    @Override
    protected int getSelectedMenuItemId() {
        return R.id.nav_dashboard;
    }

    private Button btnResolvedCases;
    private TextView txtPending;
    private TextView txtHighPriority;

    private FirebaseFirestore db;
    private LoadingDialog loadingDialog;
    private RecyclerView dashboardDeploymentRecycler;
    private List<DeploymentModel> dashboardDeployments;
    private DeploymentAdapter dashboardAdapter;
    private TextView txtResolved; // This line remains unchanged
    private TextView txtCurrentLocation; // New field added

    private FusedLocationProviderClient fusedLocationClient;
    private static final int LOCATION_PERMISSION_REQUEST_CODE = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        btnResolvedCases = findViewById(R.id.btnResolvedCases);
        txtPending = findViewById(R.id.txtPending);
        txtHighPriority = findViewById(R.id.txtHighPriority);

        db = FirebaseFirestore.getInstance();
        loadingDialog = new LoadingDialog(this);

        // Setup dashboard deployments list
        dashboardDeploymentRecycler = findViewById(R.id.dashboardDeploymentRecycler);
        dashboardDeploymentRecycler.setLayoutManager(new androidx.recyclerview.widget.LinearLayoutManager(this));
        dashboardDeployments = new java.util.ArrayList<>();
        dashboardAdapter = new DeploymentAdapter(dashboardDeployments, (deployment, position) -> showDeploymentActions(deployment));
        dashboardDeploymentRecycler.setAdapter(dashboardAdapter);

        txtCurrentLocation = findViewById(R.id.txtCurrentLocation); // Initialize new field
        fusedLocationClient = LocationServices.getFusedLocationProviderClient(this);

        // Check and request location permission
        checkLocationPermission();

        // Load stats from Firestore
        loadDashboardStats();

        loadDashboardDeployments();
    }

    private void checkLocationPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.ACCESS_FINE_LOCATION},
                    LOCATION_PERMISSION_REQUEST_CODE);
        } else {
            getLastLocation();
        }
    }

    private void getLastLocation() {
        if (ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED && ActivityCompat.checkSelfPermission(this, Manifest.permission.ACCESS_COARSE_LOCATION) != PackageManager.PERMISSION_GRANTED) {
            return;
        }
        fusedLocationClient.getLastLocation()
                .addOnSuccessListener(this, location -> {
                    if (location != null) {
                        updateLocationUI(location);
                    } else {
                        txtCurrentLocation.setText("📍 Location: Unknown");
                    }
                });
    }

    private void updateLocationUI(Location location) {
        Geocoder geocoder = new Geocoder(this, Locale.getDefault());
        try {
            List<Address> addresses = geocoder.getFromLocation(location.getLatitude(), location.getLongitude(), 1);
            if (addresses != null && !addresses.isEmpty()) {
                Address address = addresses.get(0);
                String locationName = address.getLocality() != null ? address.getLocality() : address.getSubAdminArea();
                if (locationName == null) locationName = address.getAdminArea();
                txtCurrentLocation.setText("📍 " + locationName);
            } else {
                txtCurrentLocation.setText("📍 Lat: " + location.getLatitude() + ", Lon: " + location.getLongitude());
            }
        } catch (IOException e) {
            txtCurrentLocation.setText("📍 Lat: " + location.getLatitude() + ", Lon: " + location.getLongitude());
        }
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions, @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == LOCATION_PERMISSION_REQUEST_CODE) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                getLastLocation();
            } else {
                Toast.makeText(this, "Location permission denied", Toast.LENGTH_SHORT).show();
                txtCurrentLocation.setText("📍 Location: Permission Denied");
            }
        }
    }

    private void loadDashboardDeployments() {
        loadingDialog.show();

        db.collection("deployments")
                .limit(6)
                .get()
                .addOnSuccessListener(queryDocumentSnapshots -> {
                    dashboardDeployments.clear();

                    for (var document : queryDocumentSnapshots) {
                        String hotspot = document.getString("hotspot");
                        String station = document.getString("police_station");
                        String vehicle = document.getString("vehicle");
                        String status = document.getString("status");
                        Long officers = document.getLong("officers_required");
                        Long violations = document.getLong("violations");
                        Long timestamp = document.getLong("timestamp");

                        dashboardDeployments.add(new DeploymentModel(
                                document.getId(),
                                hotspot,
                                station,
                                vehicle,
                                status,
                                officers == null ? 0 : officers,
                                violations == null ? 0 : violations,
                                timestamp == null ? 0 : timestamp
                        ));
                    }

                    dashboardAdapter.notifyDataSetChanged();
                    loadingDialog.hide();
                })
                .addOnFailureListener(e -> loadingDialog.hide());
    }

    private void showDeploymentActions(DeploymentModel deployment) {
        // Build detailed deployment info message
        String detailsMessage = String.format(
                "📍 Location: %s\n" +
                "👮 Station: %s\n" +
                "🚔 Officers: %d\n" +
                "🚓 Vehicle: %s\n" +
                "✅ Status: %s\n" +
                "⚠️ Violations: %d",
                deployment.getHotspot(),
                deployment.getPolice_station(),
                deployment.getOfficers_required(),
                deployment.getVehicle(),
                deployment.getStatus(),
                deployment.getViolations()
        );

        android.app.AlertDialog.Builder builder = new android.app.AlertDialog.Builder(this);
        builder.setTitle("Deployment Details");
        builder.setMessage(detailsMessage);
        
        builder.setPositiveButton("Edit Officers", (dialog, which) -> {
            android.widget.EditText input = new android.widget.EditText(this);
            input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
            input.setHint(String.valueOf(deployment.getOfficers_required()));

            new android.app.AlertDialog.Builder(this)
                    .setTitle("Edit Officers")
                    .setView(input)
                    .setPositiveButton("Save", (d, i) -> {
                        String text = input.getText().toString().trim();
                        if (!text.isEmpty()) {
                            try {
                                long newCount = Long.parseLong(text);
                                db.collection("deployments").document(deployment.getId())
                                        .update("officers_required", newCount)
                                        .addOnSuccessListener(aVoid -> {
                                            Toast.makeText(DashboardActivity.this, "Officers updated", Toast.LENGTH_SHORT).show();
                                            loadDashboardDeployments();
                                        })
                                        .addOnFailureListener(e -> Toast.makeText(DashboardActivity.this, "Failed to update", Toast.LENGTH_SHORT).show());
                            } catch (NumberFormatException e) {
                                Toast.makeText(DashboardActivity.this, "Invalid number", Toast.LENGTH_SHORT).show();
                            }
                        }
                    })
                    .setNegativeButton("Cancel", null)
                    .show();
        });

        builder.setNegativeButton("Undeploy", (dialog, which) -> {
            new android.app.AlertDialog.Builder(this)
                    .setTitle("Confirm Undeploy")
                    .setMessage("Remove this deployment from " + deployment.getHotspot() + "?")
                    .setPositiveButton("Yes", (d, i) -> {
                        loadingDialog.show();
                        db.collection("deployments").document(deployment.getId())
                                .delete()
                                .addOnSuccessListener(aVoid -> {
                                    Toast.makeText(DashboardActivity.this, "Deployment removed", Toast.LENGTH_SHORT).show();
                                    loadDashboardDeployments();
                                })
                                .addOnFailureListener(e -> {
                                    loadingDialog.hide();
                                    Toast.makeText(DashboardActivity.this, "Failed to remove", Toast.LENGTH_SHORT).show();
                                });
                    })
                    .setNegativeButton("Cancel", null)
                    .show();
        });

        builder.setNeutralButton("Close", null);
        builder.show();
    }

    private void loadDashboardStats() {
        loadingDialog.show();

        db.collection("hotspots")
                .get()
                .addOnSuccessListener(queryDocumentSnapshots -> {
                    int totalHotspots = 0;
                       int criticalHotspots = 0;

                    for (var document : queryDocumentSnapshots) {
                        totalHotspots++;

                        Double score = document.getDouble("dynamic_priority_score");
                        if (score != null && score >= 0.85) {
                            criticalHotspots++;
                        }

                           // We no longer display total violations on the dashboard.
                    }

                    txtPending.setText(String.valueOf(totalHotspots));
                    txtHighPriority.setText(String.valueOf(criticalHotspots));
                       // txtResolved is no longer used since total violations are not displayed.
                    loadingDialog.hide();
                })
                .addOnFailureListener(e -> loadingDialog.hide());
    }
}
