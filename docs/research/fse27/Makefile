PAPER = paper

all: $(PAPER).pdf

$(PAPER).pdf: $(PAPER).tex references.bib
	pdflatex -interaction=nonstopmode $(PAPER)
	bibtex $(PAPER)
	pdflatex -interaction=nonstopmode $(PAPER)
	pdflatex -interaction=nonstopmode $(PAPER)

pages: $(PAPER).pdf
	@pdfinfo $(PAPER).pdf | grep Pages

todo:
	@grep -o 'TODO(data)[^]]*\|TODOdata{[^}]*}\|TODOcheck{[^}]*}' $(PAPER).tex | sort | uniq -c

clean:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log $(PAPER).out $(PAPER).cut

.PHONY: all pages todo clean
