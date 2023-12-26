LANGFILES := $(shell find lang/*.ts)

.DEFAULT_GOAL := default
.PHONY: default
default: $(LANGFILES:.ts=.qm)

lang/%.qm : lang/%.ts
	lrelease $<
