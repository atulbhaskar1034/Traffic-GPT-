package com.example.parkiqpolice;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;

public class DeploymentAdapter
        extends RecyclerView.Adapter<DeploymentAdapter.ViewHolder> {

    private final List<DeploymentModel> deploymentList;
        private final OnItemClickListener listener;

        public interface OnItemClickListener {
                void onItemClick(DeploymentModel deployment, int position);
        }

        public DeploymentAdapter(List<DeploymentModel> deploymentList) {
                this(deploymentList, null);
        }

        public DeploymentAdapter(List<DeploymentModel> deploymentList, OnItemClickListener listener) {
                this.deploymentList = deploymentList;
                this.listener = listener;
        }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(
            @NonNull ViewGroup parent,
            int viewType
    ) {

        View view = LayoutInflater.from(parent.getContext())
                .inflate(
                        R.layout.deployment_card,
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

        DeploymentModel deployment =
                deploymentList.get(position);

        holder.txtHotspot.setText(
                "📍 " + deployment.getHotspot()
        );

        holder.txtOfficers.setText(
                "🚔 Officers: "
                        + deployment.getOfficers_required()
        );

        holder.itemView.setOnClickListener(v -> {
            if (listener != null) {
                listener.onItemClick(deployment, position);
            }
        });
    }

    @Override
    public int getItemCount() {
        return deploymentList == null ? 0 : deploymentList.size();
    }

    static class ViewHolder
            extends RecyclerView.ViewHolder {

        TextView txtHotspot;
        TextView txtOfficers;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);

            txtHotspot =
                    itemView.findViewById(R.id.txtHotspot);

            txtOfficers =
                    itemView.findViewById(R.id.txtOfficers);
        }
    }
}