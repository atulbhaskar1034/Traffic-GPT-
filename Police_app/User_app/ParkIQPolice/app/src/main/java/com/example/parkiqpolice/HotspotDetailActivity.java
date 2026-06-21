package com.example.parkiqpolice;

import android.content.Intent;
import android.net.Uri;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;

import androidx.appcompat.app.AppCompatActivity;

import com.google.android.material.card.MaterialCardView;
import com.google.firebase.firestore.FirebaseFirestore;

import java.time.LocalTime;
import java.util.HashMap;
import java.util.Map;

public class HotspotDetailActivity extends AppCompatActivity {

    FirebaseFirestore db;

    // Class variables to store the latest deployment plan values
    int approvedOfficers = 0;
    String approvedVehicle = "";

    TextView txtJunction;
    TextView txtStation;
    TextView txtStatus;
    TextView txtScore;
    TextView txtViolations;
    TextView txtPeakHour;

    Button btnMaps;
    Button btnDeploy;
    Button btnApprove;

    MaterialCardView recommendationCard;
    TextView txtRecommendation;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_hotspot_detail);

        db = FirebaseFirestore.getInstance();

        txtJunction = findViewById(R.id.txtJunction);
        txtStation = findViewById(R.id.txtStation);
        txtStatus = findViewById(R.id.txtStatus);
        txtScore = findViewById(R.id.txtScore);
        txtViolations = findViewById(R.id.txtViolations);
        txtPeakHour = findViewById(R.id.txtPeakHour);

        btnMaps = findViewById(R.id.btnMaps);
        btnDeploy = findViewById(R.id.btnDeploy);
        btnApprove = findViewById(R.id.btnApprove);
        btnApprove.setVisibility(View.GONE);

        recommendationCard = findViewById(R.id.recommendationCard);
        txtRecommendation = findViewById(R.id.txtRecommendation);

        String junction =
                getIntent().getStringExtra("junction");

        String station =
                getIntent().getStringExtra("station");

        String status =
                getIntent().getStringExtra("status");

        double score =
                getIntent().getDoubleExtra("score", 0);

        long violations =
                getIntent().getLongExtra("violations", 0);

        String peakHour =
                getIntent().getStringExtra("peakHour");

        double latitude =
                getIntent().getDoubleExtra("latitude", 0);

        double longitude =
                getIntent().getDoubleExtra("longitude", 0);

        txtJunction.setText("📍 " + junction);
        txtStation.setText(station);
        txtStatus.setText(status);

        txtScore.setText(
                String.format("%.2f", score)
        );

        txtViolations.setText(
                String.valueOf(violations)
        );

        txtPeakHour.setText(
                peakHour + ":00"
        );

        int hour = Integer.parseInt(peakHour);

        int currentHour = LocalTime.now().getHour();
        int difference = Math.abs(hour - currentHour);

        // DEPLOYMENT PLAN
        btnDeploy.setOnClickListener(v -> {

            recommendationCard.setVisibility(View.VISIBLE);

            int requiredOfficers;
            String vehicle;

            if (score >= 0.85) {

                requiredOfficers = 4;
                vehicle = "Tow Vehicle Required";

                // Store in class variables
                approvedOfficers = requiredOfficers;
                approvedVehicle = vehicle;

            } else if (score >= 0.70) {

                requiredOfficers = 3;
                vehicle = "Tow Vehicle Recommended";

                approvedOfficers = requiredOfficers;
                approvedVehicle = vehicle;

            } else if (score >= 0.50) {

                requiredOfficers = 2;
                vehicle = "Bike Patrol";

                approvedOfficers = requiredOfficers;
                approvedVehicle = vehicle;

            } else {

                requiredOfficers = 1;
                vehicle = "Routine Patrol";

                approvedOfficers = requiredOfficers;
                approvedVehicle = vehicle;
            }

            String recommendation =
                    "🚔 Officers Required: "
                            + requiredOfficers +

                            "\n\n🚓 Vehicle: "
                            + vehicle +

                            "\n\n⏰ Patrol Window: "
                            + (hour - 1)
                            + ":00 - "
                            + (hour + 1)
                            + ":00" +

                            "\n\n📋 Status: Pending Approval";

            txtRecommendation.setText(recommendation);

            // Show approve button only if peak hour is within 2 hours
            if (difference <= 2) {

                btnApprove.setVisibility(View.VISIBLE);

            } else {

                btnApprove.setVisibility(View.GONE);

                txtRecommendation.append(
                        "\n\n⚠ Deployment not required now."
                );

                txtRecommendation.append(
                        "\nPeak traffic window is outside current time."
                );
            }
        });

        // OPEN GOOGLE MAPS
        btnMaps.setOnClickListener(v -> {

            Uri gmmIntentUri = Uri.parse(
                    "google.navigation:q="
                            + latitude
                            + ","
                            + longitude
            );

            Intent mapIntent = new Intent(
                    Intent.ACTION_VIEW,
                    gmmIntentUri
            );

            mapIntent.setPackage(
                    "com.google.android.apps.maps"
            );

            if (mapIntent.resolveActivity(
                    getPackageManager()
            ) != null) {

                startActivity(mapIntent);

            } else {

                Intent browserIntent =
                        new Intent(
                                Intent.ACTION_VIEW,
                                Uri.parse(
                                        "https://www.google.com/maps/search/?api=1&query="
                                                + latitude
                                                + ","
                                                + longitude
                                )
                        );

                startActivity(browserIntent);
            }
        });

        // APPROVE DEPLOYMENT (saves to Firestore)
        btnApprove.setOnClickListener(v -> {

            Map<String, Object> deployment =
                    new HashMap<>();

            deployment.put(
                    "hotspot",
                    junction
            );

            deployment.put(
                    "police_station",
                    station
            );

            deployment.put(
                    "priority_score",
                    score
            );

            deployment.put(
                    "violations",
                    violations
            );

            deployment.put(
                    "peak_hour",
                    peakHour
            );

            // Save the officers and vehicle from the stored class variables
            deployment.put(
                    "officers_required",
                    approvedOfficers
            );

            deployment.put(
                    "vehicle",
                    approvedVehicle
            );

            deployment.put(
                    "status",
                    "APPROVED"
            );

            deployment.put(
                    "timestamp",
                    System.currentTimeMillis()
            );

            db.collection("deployments")
                    .add(deployment)
                    .addOnSuccessListener(documentReference -> {

                        btnApprove.setText(
                                "✅ Deployment Approved"
                        );

                        btnApprove.setEnabled(false);

                    });
        });
    }
}