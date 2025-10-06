all: $(patsubst %.s, %.bin, $(wildcard *.s))

%.bin: %.s assembler.py
	./assembler.py $< -o $@ -s 65536
