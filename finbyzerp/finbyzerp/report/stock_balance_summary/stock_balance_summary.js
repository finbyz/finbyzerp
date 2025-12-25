// Copyright (c) 2025, Finbyz Tech Pvt Ltd and contributors
// For license information, please see license.txt

frappe.query_reports["Stock Balance Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			fieldname: "include_zero_qty",
			label: __("Include Zero Qty"),
			fieldtype: "Check",
			default: 0
		},
		{
			fieldname: "branch",
			label: __("Branch"),
			fieldtype: "Link",
			options: "Branch"
		}
		
		
	],

	formatter: function(value, row, column, data, default_formatter) {
		let formatted = default_formatter(value, row, column, data);

		// Color qty columns: positive green, negative red, zero/default black
		const qtyFields = ["opening_balance", "inwards_qty", "outwards_qty", "qty_after_transaction"];
		if (data && column && qtyFields.includes(column.fieldname)) {
			const num = Number(data[column.fieldname]);
			if (num > 0) {
				formatted = `<span style="color: #137333;">${formatted}</span>`;
			} else if (num < 0) {
				formatted = `<span style="color: #c5221f;">${formatted}</span>`;
			}
		}

		// Highlight Grand Total row
		if (data && data.item_name && data.item_name.includes("Grand Total")) {
			formatted = `
				<span style="
					font-weight: 600;
					background-color: #f0f4f7;
					display: block;
					padding: 4px 6px;
					border-radius: 2px;
				">
					${formatted}
				</span>`;
		}

		return formatted;
	},

	onload: function(report) {
		report.page.add_inner_button(__('Refresh'), function() {
			report.refresh();
		});
	},

	after_datatable_render: function(datatable_instance) {
		add_column_group_headers(datatable_instance);
	}
};

function add_column_group_headers(datatable) {
	try {
		// Remove any existing group headers
		const existing = datatable.wrapper.querySelectorAll('.custom-column-group-header');
		existing.forEach(el => el.remove());

		// Get the header row container
		const headerRow = datatable.wrapper.querySelector('.dt-header .dt-row');
		if (!headerRow) return;

		// Get all header cells
		const headerCells = Array.from(headerRow.querySelectorAll('.dt-cell'));
		if (headerCells.length === 0) return;

		// Log column information for debugging
		console.log('Total header cells:', headerCells.length);
		
		// Find columns by their text content
		const columnIndices = {};
		headerCells.forEach((cell, index) => {
			const cellText = cell.textContent.trim();
			columnIndices[cellText] = index;
			console.log(`Column ${index}: "${cellText}"`);
		});

		// Define column groups - Opening Balance, Inwards, Outwards, Closing Balance
		const columnGroups = [];
		
		// We need to identify groups by position since all have same labels (Quantity, Rate, Value)
		// First, find where "Particulars" ends to know where our grouped columns start
		let particularsIdx = columnIndices['Particulars'];
		
		// After Particulars, we should have groups of 3 columns each
		// Count how many "Quantity" columns we have
		let quantityIndices = [];
		headerCells.forEach((cell, index) => {
			const cellText = cell.textContent.trim();
			if (cellText === 'Quantity') {
				quantityIndices.push(index);
			}
		});
		
		console.log('Quantity column indices:', quantityIndices);
		
		// Define groups based on the Quantity columns we found
		const groupLabels = ['Opening Balance', 'Inwards', 'Outwards', 'Closing Balance'];
		const groupColors = [
			{ bg: '#E8F5E9', text: '#000' },  // Green for Opening Balance
			{ bg: '#E3F2FD', text: '#000' },  // Blue for Inwards
			{ bg: '#FFF3E0', text: '#000' },  // Orange for Outwards
			{ bg: '#F3E5F5', text: '#000' }   // Purple for Closing Balance
		];
		
		quantityIndices.forEach((qtyIndex, groupIndex) => {
			if (groupIndex < groupLabels.length) {
				// Each group spans 3 columns: Quantity, Rate, Value
				columnGroups.push({
					startIndex: qtyIndex,
					endIndex: qtyIndex + 2,  // +2 to cover Quantity, Rate, Value
					label: groupLabels[groupIndex],
					bgColor: groupColors[groupIndex].bg,
					textColor: groupColors[groupIndex].text
				});
			}
		});

		console.log('Column groups:', JSON.stringify(columnGroups, null, 2));

		// Create group header row
		const groupHeaderRow = document.createElement('div');
		groupHeaderRow.className = 'dt-row custom-column-group-header';
		groupHeaderRow.style.cssText = `
			display: flex;
			border-bottom: 1px solid #d1d8dd;
			background-color: #f5f7fa;
			position: relative;
		`;

		// Create cells for each position
		headerCells.forEach((cell, index) => {
			const cellWidth = cell.offsetWidth || parseFloat(cell.style.width) || 100;
			
			// Check if this column is part of a group
			let groupInfo = null;
			for (const group of columnGroups) {
				if (index >= group.startIndex && index <= group.endIndex) {
					groupInfo = group;
					break;
				}
			}

			// If it's the start of a group, create a spanning cell
			if (groupInfo && index === groupInfo.startIndex) {
				// Calculate total width for the group
				let totalWidth = 0;
				for (let i = groupInfo.startIndex; i <= groupInfo.endIndex && i < headerCells.length; i++) {
					totalWidth += headerCells[i].offsetWidth || parseFloat(headerCells[i].style.width) || 100;
				}

				const groupCell = document.createElement('div');
				groupCell.className = 'dt-cell group-header-cell';
				groupCell.style.cssText = `
					width: ${totalWidth}px;
					min-width: ${totalWidth}px;
					max-width: ${totalWidth}px;
					padding: 8px 4px;
					text-align: center;
					font-weight: 600;
					font-size: 12px;
					background-color: ${groupInfo.bgColor};
					color: ${groupInfo.textColor};
					border-right: 1px solid #d1d8dd;
					display: flex;
					align-items: center;
					justify-content: center;
					box-sizing: border-box;
				`;
				groupCell.textContent = groupInfo.label;
				groupHeaderRow.appendChild(groupCell);
			} 
			// If it's a middle column of a group, skip it
			else if (groupInfo && index > groupInfo.startIndex && index <= groupInfo.endIndex) {
				// Skip - this column is covered by the group header
			}
			// Otherwise create an empty cell
			else {
				const emptyCell = document.createElement('div');
				emptyCell.className = 'dt-cell';
				emptyCell.style.cssText = `
					width: ${cellWidth}px;
					min-width: ${cellWidth}px;
					max-width: ${cellWidth}px;
					padding: 8px 4px;
					border-right: 1px solid #d1d8dd;
					box-sizing: border-box;
				`;
				emptyCell.innerHTML = '&nbsp;';
				groupHeaderRow.appendChild(emptyCell);
			}
		});

		// Insert the group header row above the regular header
		const headerContainer = headerRow.parentElement;
		headerContainer.insertBefore(groupHeaderRow, headerRow);

		// Add custom styles
		if (!document.getElementById('stock-balance-summary-styles')) {
			const style = document.createElement('style');
			style.id = 'stock-balance-summary-styles';
			style.textContent = `
				.custom-column-group-header {
					min-height: 35px;
				}
				.custom-column-group-header .group-header-cell {
					font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
				}
			`;
			document.head.appendChild(style);
		}

	} catch (error) {
		console.error('Error adding column group headers:', error);
	}
}