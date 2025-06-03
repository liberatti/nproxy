import {Component, OnInit} from '@angular/core';
import {FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatOptionModule} from '@angular/material/core';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatTooltipModule} from '@angular/material/tooltip';
import {RouterModule} from '@angular/router';
import ChartDataLabels from "chartjs-plugin-datalabels";
import Chart from "chart.js/auto";
import Zoom from "chartjs-plugin-zoom";
import {ClusterService} from "../../services/cluster.service";
import {CommonModule, NgForOf} from "@angular/common";
import {DateFormatPipe} from "../../pipes/date_format.pipe";
import {MatChip} from "@angular/material/chips";
import {MatDialog} from "@angular/material/dialog";
import {NodeDetailsDialogComponent} from "../../components/node-details-dialog/node-details-dialog.component";
import {NodeStatus} from "../../models/upstream";
import {ByteFormatPipe} from "../../pipes/format_bytes.pipe";

@Component({
    selector: 'app-account-form',
    standalone: true,
    imports: [RouterModule, FormsModule, ReactiveFormsModule, CommonModule,
        MatIconModule, MatButtonModule, MatFormFieldModule,
        MatCardModule, MatProgressBarModule, MatInputModule, MatTooltipModule,
        MatSelectModule, MatOptionModule, MatGridListModule, NgForOf, DateFormatPipe, MatChip, ByteFormatPipe
    ],

    templateUrl: './dashboard-home.component.html',
    styleUrl: './dashboard-home.component.css'
})
export class DashboardHomeComponent implements OnInit {
    nodeList: Array<NodeStatus> = [];

    constructor(
        private clusterService: ClusterService,
        private detailsDialog: MatDialog) {
        Chart.register(ChartDataLabels);
        Chart.register(Zoom);
    }

    ngOnInit(): void {
        this.refresh_nodes();
    }

    remove_node() {

    }

    show_details(nodeData: NodeStatus) {
        this.detailsDialog.open(NodeDetailsDialogComponent, {
            data: nodeData,
            width: '450px'
        });
    }

    refresh_nodes() {
        this.clusterService.getNodes().subscribe(data => {
            this.nodeList = data.data;
        });
    }
}
