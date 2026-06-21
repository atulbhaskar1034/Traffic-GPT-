package com.example.parkiqpolice;

import android.content.Intent;
import android.net.Uri;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.google.firebase.firestore.FirebaseFirestore;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class CommunityAdapter
        extends RecyclerView.Adapter<CommunityAdapter.ViewHolder> {

    List<CommunityModel> reportList;

    public CommunityAdapter(
            List<CommunityModel> reportList
    ) {
        this.reportList = reportList;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(
            @NonNull ViewGroup parent,
            int viewType
    ) {

        View view =
                LayoutInflater.from(parent.getContext())
                        .inflate(
                                R.layout.community_card,
                                parent,
                                false
                        );

        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(
            @NonNull ViewHolder holder,
            int position
    ) {
        CommunityModel report =
                reportList.get(position);

        holder.txtViolation.setText(
                "🚨 " + report.getType()
        );

        holder.txtLocation.setText(
                "📍 " + report.getLocation()
        );

        holder.txtVehicle.setText(
                "🚗 " + report.getVehicleType()
        );

        holder.txtScore.setText(
                "🔥 Score: "
                        + report.getScoreAwarded()
        );

        holder.txtStatus.setText(
                "✅ " + report.getStatus()
        );

                // show formatted time if available
                long ts = report.getTimestamp();
                if (ts > 0) {
                        SimpleDateFormat fmt = new SimpleDateFormat("dd MMM yyyy, HH:mm", Locale.getDefault());
                        String when = fmt.format(new Date(ts));
                        holder.txtTime.setText("🕒 " + when);
                } else {
                        holder.txtTime.setText("");
                }

        // --- Map Button Logic ---
        holder.btnMap.setOnClickListener(v -> {

            String uri =
                    "google.navigation:q="
                            + report.getLatitude()
                            + ","
                            + report.getLongitude();

            Intent mapIntent =
                    new Intent(
                            Intent.ACTION_VIEW,
                            Uri.parse(uri)
                    );

            mapIntent.setPackage(
                    "com.google.android.apps.maps"
            );

            v.getContext().startActivity(
                    mapIntent
            );
        });

        // --- Hotspot Button Logic ---
        holder.btnHotspot.setOnClickListener(v -> {

            FirebaseFirestore db =
                    FirebaseFirestore.getInstance();

            Map<String, Object> candidate =
                    new HashMap<>();

            candidate.put(
                    "source",
                    "COMMUNITY"
            );

            candidate.put(
                    "type",
                    report.getType()
            );

            candidate.put(
                    "location",
                    report.getLocation()
            );

            candidate.put(
                    "latitude",
                    report.getLatitude()
            );

            candidate.put(
                    "longitude",
                    report.getLongitude()
            );

            candidate.put(
                    "vehicleType",
                    report.getVehicleType()
            );

            candidate.put(
                    "score",
                    report.getScoreAwarded()
            );

            candidate.put(
                    "status",
                    "PENDING_REVIEW"
            );

            candidate.put(
                    "timestamp",
                    System.currentTimeMillis()
            );

            db.collection("community_candidates")
                    .add(candidate)
                    .addOnSuccessListener(documentReference -> {

                        Toast.makeText(
                                v.getContext(),
                                "🔥 Hotspot Candidate Created",
                                Toast.LENGTH_SHORT
                        ).show();

                    });
        });
    }

    @Override
    public int getItemCount() {
        return reportList.size();
    }

    static class ViewHolder
            extends RecyclerView.ViewHolder {

        TextView txtViolation;
        TextView txtLocation;
        TextView txtVehicle;
        TextView txtScore;
        TextView txtStatus;
                TextView txtTime;

        Button btnMap;
        Button btnHotspot;

        public ViewHolder(
                @NonNull View itemView
        ) {
            super(itemView);

            txtViolation =
                    itemView.findViewById(R.id.txtViolation);

                txtTime = itemView.findViewById(R.id.txtTime);

            txtLocation =
                    itemView.findViewById(R.id.txtLocation);

            txtVehicle =
                    itemView.findViewById(R.id.txtVehicle);

            txtScore =
                    itemView.findViewById(R.id.txtScore);

            txtStatus =
                    itemView.findViewById(R.id.txtStatus);

            btnMap =
                    itemView.findViewById(R.id.btnMap);

            btnHotspot =
                    itemView.findViewById(R.id.btnHotspot);
        }
    }
}