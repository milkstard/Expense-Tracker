// main.js — students will add JavaScript here as features are built

(function () {
    "use strict";

    // Inline row editing on the profile page's transactions table
    // (Step 08 — edit expense). No-op on any page without that table.
    var table = document.querySelector("[data-txn-table]");
    if (!table) return;

    var categories = [];
    try {
        categories = JSON.parse(table.dataset.categories || "[]");
    } catch (err) {
        categories = [];
    }

    // The row currently in edit mode, plus what its cells looked like
    // before editing started, so Cancel can put them back exactly.
    var currentEdit = null;

    function buildCategorySelect(selected) {
        var select = document.createElement("select");
        select.className = "txn-input form-select";
        select.name = "category";
        categories.forEach(function (name) {
            var option = document.createElement("option");
            option.value = name;
            option.textContent = name;
            if (name === selected) option.selected = true;
            select.appendChild(option);
        });
        return select;
    }

    function buildInput(type, value, extra) {
        var input = document.createElement("input");
        input.type = type;
        input.className = "txn-input";
        input.value = value;
        if (extra) {
            Object.keys(extra).forEach(function (key) {
                input[key] = extra[key];
            });
        }
        return input;
    }

    function submitTo(url, values) {
        var form = document.createElement("form");
        form.method = "POST";
        form.action = url + window.location.search;
        form.style.display = "none";

        Object.keys(values).forEach(function (name) {
            var hidden = document.createElement("input");
            hidden.type = "hidden";
            hidden.name = name;
            hidden.value = values[name];
            form.appendChild(hidden);
        });

        document.body.appendChild(form);
        form.submit();
    }

    function closeEditor() {
        if (!currentEdit) return;
        var row = currentEdit.row;
        var original = currentEdit.original;

        row.cells[0].innerHTML = original.date;
        row.cells[1].innerHTML = original.description;
        row.cells[2].innerHTML = original.category;
        row.cells[3].innerHTML = original.amount;
        row.cells[4].innerHTML = original.actions;
        row.classList.remove("txn-row--editing");
        row.removeEventListener("keydown", currentEdit.onKeydown);

        currentEdit = null;
    }

    function openEditor(row) {
        if (currentEdit) {
            if (currentEdit.row === row) return;
            closeEditor();
        }

        var cells = row.cells;
        var original = {
            date: cells[0].innerHTML,
            description: cells[1].innerHTML,
            category: cells[2].innerHTML,
            amount: cells[3].innerHTML,
            actions: cells[4].innerHTML,
        };

        var dateInput = buildInput("date", row.dataset.rawDate);
        var descInput = buildInput("text", row.dataset.rawDescription, {
            placeholder: "Description",
        });
        var categorySelect = buildCategorySelect(row.dataset.category);
        var amountInput = buildInput("number", row.dataset.rawAmount, {
            step: "0.01",
            min: "0.01",
        });

        cells[0].innerHTML = "";
        cells[0].appendChild(dateInput);
        cells[1].innerHTML = "";
        cells[1].appendChild(descInput);
        cells[2].innerHTML = "";
        cells[2].appendChild(categorySelect);
        cells[3].innerHTML = "";
        cells[3].appendChild(amountInput);

        var saveBtn = document.createElement("button");
        saveBtn.type = "button";
        saveBtn.className = "btn-primary btn-sm";
        saveBtn.textContent = "Save";

        var cancelBtn = document.createElement("button");
        cancelBtn.type = "button";
        cancelBtn.className = "btn-ghost btn-sm";
        cancelBtn.textContent = "Cancel";

        cells[4].innerHTML = "";
        cells[4].appendChild(saveBtn);
        cells[4].appendChild(cancelBtn);

        function doSave() {
            submitTo(row.dataset.editUrl, {
                amount: amountInput.value,
                category: categorySelect.value,
                date: dateInput.value,
                description: descInput.value,
            });
        }

        saveBtn.addEventListener("click", doSave);
        cancelBtn.addEventListener("click", closeEditor);

        function onKeydown(event) {
            if (event.key === "Escape") {
                closeEditor();
            } else if (event.key === "Enter" && event.target.tagName !== "SELECT") {
                event.preventDefault();
                doSave();
            }
        }
        row.addEventListener("keydown", onKeydown);

        row.classList.add("txn-row--editing");
        currentEdit = { row: row, original: original, onKeydown: onKeydown };
        amountInput.focus();
    }

    table.addEventListener("click", function (event) {
        var editLink = event.target.closest("[data-txn-edit]");
        if (editLink) {
            event.preventDefault();
            var editRow = editLink.closest("tr");
            if (editRow) openEditor(editRow);
            return;
        }

        var deleteBtn = event.target.closest("[data-txn-delete]");
        if (deleteBtn) {
            var deleteRow = deleteBtn.closest("tr");
            if (!deleteRow) return;
            var label = deleteRow.dataset.rawDescription || (deleteRow.dataset.category + " expense");
            if (window.confirm('Delete "' + label + '"? This cannot be undone.')) {
                submitTo(deleteRow.dataset.deleteUrl, {});
            }
        }
    });

    // The server names a row to reopen via data-edit-id — either a
    // typed/bookmarked /expenses/<id>/edit URL, or a failed save re-render.
    var initialEditId = table.dataset.editId;
    if (initialEditId) {
        var initialRow = table.querySelector('tr[data-id="' + initialEditId + '"]');
        if (initialRow) openEditor(initialRow);
    }
})();
