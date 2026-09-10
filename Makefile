.PHONY: figure1 figure2 clean-cache

data/000941/000941:
	mkdir -p data/000941
	dandi download -o data/000941 https://dandiarchive.org/dandiset/000941/draft

data/000953/000953:
	mkdir -p data/000953
	dandi download -o data/000953 https://dandiarchive.org/dandiset/000953/draft

# Week 1 deliverable: M1 degradation curve, frozen Wiener filter.
figure1: data/000941/000941
	python3 -m src.figures --dataset m1 --out figures/fig1_degradation_m1.png

# Week 2: extends the same pipeline to M2.
figure2: data/000953/000953
	python3 -m src.figures --dataset m2 --out figures/fig2_degradation_m2.png

clean-cache:
	rm -f cache/*.npz cache/*.joblib
