package com.example.parkiqpolice;

import android.content.Intent;
import android.graphics.Color;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class HotspotAdapter
        extends RecyclerView.Adapter<HotspotAdapter.ViewHolder> {

    private final List<HotspotModel> hotspotList;

    public HotspotAdapter(List<HotspotModel> hotspotList) {
        this.hotspotList = hotspotList;
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(
            @NonNull ViewGroup parent,
            int viewType
    ) {

        View view = LayoutInflater.from(parent.getContext())
                .inflate(
                        R.layout.hotspot_card,
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

        HotspotModel hotspot = hotspotList.get(position);

        // txtRank removed

        holder.txtJunction.setText(
                hotspot.getJunctionName()
        );

        holder.txtStation.setText(
                "👮 " + hotspot.getPoliceStation()
        );

        holder.txtPriority.setText(
                hotspot.getPriorityLevel()
        );

        String level = hotspot.getPriorityLevel();

        if (level != null) {

            if (level.equalsIgnoreCase("VERY_HIGH")) {

                holder.txtPriority.setBackgroundColor(
                        Color.parseColor("#D32F2F")
                );

            } else if (level.equalsIgnoreCase("HIGH")) {

                holder.txtPriority.setBackgroundColor(
                        Color.parseColor("#F57C00")
                );

            } else if (level.equalsIgnoreCase("MEDIUM")) {

                holder.txtPriority.setBackgroundColor(
                        Color.parseColor("#FBC02D")
                );

            } else {

                holder.txtPriority.setBackgroundColor(
                        Color.parseColor("#388E3C")
                );
            }
        }

        holder.txtScore.setText(
                "⭐ " + String.format("%.2f",
                        hotspot.getPriorityScore())
        );

        holder.txtViolations.setText(
                "🚨 " + hotspot.getViolations()
        );

        // Improved peak hour display with ":00"
        holder.txtPeakHour.setText(
                "🕒 Peak Traffic Hour: "
                        + hotspot.getPeakHour()
                        + ":00"
        );

        // --- NEW: Risk-based status using priority score ---
        double score = hotspot.getPriorityScore();

        if (score >= 0.85) {

            holder.txtStatus.setText(
                    "🔴 CRITICAL"
            );

            holder.txtStatus.setTextColor(
                    Color.parseColor("#D32F2F")
            );

        } else if (score >= 0.70) {

            holder.txtStatus.setText(
                    "🟠 HIGH RISK"
            );

            holder.txtStatus.setTextColor(
                    Color.parseColor("#F57C00")
            );

        } else if (score >= 0.50) {

            holder.txtStatus.setText(
                    "🟡 MEDIUM RISK"
            );

            holder.txtStatus.setTextColor(
                    Color.parseColor("#FBC02D")
            );

        } else {

            holder.txtStatus.setText(
                    "🟢 LOW RISK"
            );

            holder.txtStatus.setTextColor(
                    Color.parseColor("#388E3C")
            );
        }

        holder.itemView.setOnClickListener(v -> {

            Intent intent =
                    new Intent(
                            v.getContext(),
                            HotspotDetailActivity.class
                    );

            intent.putExtra(
                    "junction",
                    hotspot.getJunctionName()
            );

            intent.putExtra(
                    "station",
                    hotspot.getPoliceStation()
            );

            intent.putExtra(
                    "score",
                    hotspot.getPriorityScore()
            );

            intent.putExtra(
                    "violations",
                    hotspot.getViolations()
            );

            intent.putExtra(
                    "peakHour",
                    hotspot.getPeakHour()
            );

            intent.putExtra(
                    "status",
                    holder.txtStatus.getText().toString()
            );

            intent.putExtra(
                    "latitude",
                    hotspot.getLatitude()
            );

            intent.putExtra(
                    "longitude",
                    hotspot.getLongitude()
            );

            v.getContext().startActivity(intent);
        });
    }

    @Override
    public int getItemCount() {
        return hotspotList.size();
    }

    static class ViewHolder extends RecyclerView.ViewHolder {

        // txtRank removed
        TextView txtJunction;
        TextView txtStation;
        TextView txtPriority;
        TextView txtScore;
        TextView txtViolations;
        TextView txtPeakHour;
        TextView txtStatus;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);

            // txtRank = itemView.findViewById(R.id.txtRank); removed
            txtJunction = itemView.findViewById(R.id.txtJunction);
            txtStation = itemView.findViewById(R.id.txtStation);
            txtPriority = itemView.findViewById(R.id.txtPriority);
            txtScore = itemView.findViewById(R.id.txtScore);
            txtViolations = itemView.findViewById(R.id.txtViolations);
            txtPeakHour = itemView.findViewById(R.id.txtPeakHour);
            txtStatus = itemView.findViewById(R.id.txtStatus);
        }
    }
}