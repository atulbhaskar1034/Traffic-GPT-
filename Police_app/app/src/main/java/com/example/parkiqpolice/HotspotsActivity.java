package com.example.parkiqpolice;

import android.graphics.Color;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.MenuItem;
import android.view.View;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.PopupMenu;

import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import com.google.firebase.firestore.FirebaseFirestore;
import com.google.firebase.firestore.Query;
import com.google.firebase.firestore.QueryDocumentSnapshot;

import java.time.LocalTime;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

public class HotspotsActivity extends BaseNavigationActivity {

    private static final int SORT_RELEVANCE = 0;
    private static final int SORT_NEAREST = 1;
    private static final int SORT_TIME = 2;
    private static final int SORT_SCORE = 3;
    private static final int SORT_HIGH_RISK = 4;

    private RecyclerView hotspotRecycler;
    private EditText edtSearchHotspot;
        private ImageButton btnSortHotspot;
    private FirebaseFirestore db;
    private List<HotspotModel> allHotspots;
    private List<HotspotModel> hotspotList;
    private HotspotAdapter adapter;
    private LoadingDialog loadingDialog;
    private String currentSearchQuery = "";
    private int currentSortOrder = SORT_RELEVANCE;
    private int currentHour;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        hotspotRecycler = findViewById(R.id.hotspotRecycler);
        edtSearchHotspot = findViewById(R.id.edtSearchHotspot);
        btnSortHotspot = findViewById(R.id.btnSortHotspot);

        hotspotRecycler.setLayoutManager(
                new LinearLayoutManager(this)
        );

        allHotspots = new ArrayList<>();
        hotspotList = new ArrayList<>();

        adapter = new HotspotAdapter(hotspotList);
        hotspotRecycler.setAdapter(adapter);

        db = FirebaseFirestore.getInstance();
        loadingDialog = new LoadingDialog(this);

        setupSearchAndSort();
        loadHotspots();
    }

    @Override
    protected int getContentLayoutId() {
        return R.layout.activity_hotspots;
    }

    @Override
    protected int getSelectedMenuItemId() {
        return R.id.nav_hotspots;
    }

    private void setupSearchAndSort() {
                // show a compact sort popup when the small sort button is clicked
                btnSortHotspot.setOnClickListener(new View.OnClickListener() {
                        @Override
                        public void onClick(View v) {
                                PopupMenu popup = new PopupMenu(HotspotsActivity.this, v);
                                String[] options = getResources().getStringArray(R.array.hotspot_sort_options);
                                for (int i = 0; i < options.length; i++) {
                                        popup.getMenu().add(0, i, i, options[i]);
                                }
                                popup.setOnMenuItemClickListener(new PopupMenu.OnMenuItemClickListener() {
                                        @Override
                                        public boolean onMenuItemClick(MenuItem item) {
                                                currentSortOrder = item.getItemId();
                                                applyFilters();
                                                return true;
                                        }
                                });
                                popup.show();
                        }
                });

        edtSearchHotspot.addTextChangedListener(
                new TextWatcher() {
                    @Override
                    public void beforeTextChanged(CharSequence s,
                                                  int start,
                                                  int count,
                                                  int after) {
                    }

                    @Override
                    public void onTextChanged(CharSequence s,
                                              int start,
                                              int before,
                                              int count) {
                        currentSearchQuery = s.toString();
                        applyFilters();
                    }

                    @Override
                    public void afterTextChanged(Editable s) {
                    }
                }
        );
    }

    private void loadHotspots() {
        loadingDialog.show();

        currentHour = LocalTime.now().getHour();

        db.collection("hotspots")
                .orderBy(
                        "dynamic_priority_score",
                        Query.Direction.DESCENDING
                )
                .limit(300)
                .get()
                .addOnSuccessListener(queryDocumentSnapshots -> {

                    allHotspots.clear();
                    hotspotList.clear();

                    List<HotspotModel> relevantHotspots =
                            new ArrayList<>();

                    List<HotspotModel> backupHotspots =
                            new ArrayList<>();

                    for (QueryDocumentSnapshot document
                            : queryDocumentSnapshots) {

                        String junction =
                                document.getString("junction_name");

                        if (junction == null
                                || junction.trim().isEmpty()
                                || junction.equalsIgnoreCase("No Junction")) {

                            junction =
                                    "📍 Area Monitoring Zone";
                        }

                        Object peakHourObj =
                                document.get("peak_hour");

                        if (peakHourObj == null) {
                            continue;
                        }

                        int peakHour;

                        try {

                            peakHour =
                                    Integer.parseInt(
                                            peakHourObj.toString()
                                    );

                        } catch (Exception e) {
                            continue;
                        }

                        String station =
                                document.getString("police_station");

                        String priorityLevel =
                                document.getString("priority_level");

                        Double priorityScore =
                                document.getDouble(
                                        "dynamic_priority_score"
                                );

                        Long violations =
                                document.getLong("violations");

                        Long rank =
                                document.getLong("rank");

                        Double latitude =
                                document.getDouble("latitude");

                        Double longitude =
                                document.getDouble("longitude");

                        HotspotModel hotspot =
                                new HotspotModel(
                                        junction,
                                        station,
                                        priorityLevel,
                                        priorityScore == null ? 0 : priorityScore,
                                        violations == null ? 0 : violations,
                                        String.valueOf(peakHour),
                                        rank == null ? 0 : rank,
                                        latitude == null ? 0 : latitude,
                                        longitude == null ? 0 : longitude
                                );

                        int difference =
                                Math.abs(
                                        peakHour - currentHour
                                );

                        if (difference <= 4) {
                            relevantHotspots.add(hotspot);
                        } else {
                            backupHotspots.add(hotspot);
                        }
                    }

                    allHotspots.addAll(relevantHotspots);
                    for (HotspotModel hotspot : backupHotspots) {
                        if (allHotspots.size() >= 20) {
                            break;
                        }
                        allHotspots.add(hotspot);
                    }

                    applyFilters();
                    loadingDialog.hide();
                })
                .addOnFailureListener(e -> loadingDialog.hide());
    }

    private void applyFilters() {
        hotspotList.clear();

        String query = currentSearchQuery.trim().toLowerCase();
        for (HotspotModel hotspot : allHotspots) {
            if (query.isEmpty()
                    || hotspot.getJunctionName().toLowerCase().contains(query)
                    || hotspot.getPoliceStation().toLowerCase().contains(query)) {
                hotspotList.add(hotspot);
            }
        }

        switch (currentSortOrder) {
            case SORT_NEAREST:
                Collections.sort(hotspotList,
                        Comparator.comparingLong(h -> h.getRank()));
                break;
            case SORT_TIME:
                Collections.sort(hotspotList,
                        Comparator.comparingLong(h -> {
                            try {
                                return Math.abs(
                                        Long.parseLong(h.getPeakHour())
                                                - currentHour);
                            } catch (NumberFormatException e) {
                                return Long.MAX_VALUE;
                            }
                        }));
                break;
            case SORT_SCORE:
                Collections.sort(hotspotList,
                        Comparator.comparingDouble(
                                HotspotModel::getPriorityScore
                        ).reversed());
                break;
            case SORT_HIGH_RISK:
                Collections.sort(hotspotList,
                        Comparator.comparingDouble(
                                HotspotModel::getPriorityScore
                        ).reversed());
                break;
            case SORT_RELEVANCE:
            default:
                // Keep original ordering
                break;
        }

        adapter.notifyDataSetChanged();
    }
}