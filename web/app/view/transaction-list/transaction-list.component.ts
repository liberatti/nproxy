import {Component, OnInit, signal, ViewChild} from '@angular/core';
import {MatTableDataSource, MatTableModule} from '@angular/material/table';
import {MatPaginatorModule, PageEvent} from '@angular/material/paginator';
import {MatDialog} from '@angular/material/dialog';
import {BreakpointObserver, Breakpoints} from '@angular/cdk/layout';
import {CommonModule} from '@angular/common';
import {FormControl, FormGroup, FormsModule, ReactiveFormsModule} from '@angular/forms';
import {MatMomentDateModule} from '@angular/material-moment-adapter';
import {MatButtonModule} from '@angular/material/button';
import {MatCardModule} from '@angular/material/card';
import {MatChipsModule} from '@angular/material/chips';
import {MatFormFieldModule} from '@angular/material/form-field';
import {MatIconModule} from '@angular/material/icon';
import {MatInputModule} from '@angular/material/input';
import {MatListModule} from '@angular/material/list';
import {MatMenuModule} from '@angular/material/menu';
import {MatProgressBarModule} from '@angular/material/progress-bar';
import {MatSelectModule} from '@angular/material/select';
import {MatSidenavModule} from '@angular/material/sidenav';
import {MatSlideToggleModule} from '@angular/material/slide-toggle';
import {MatSortModule} from '@angular/material/sort';
import {MatTooltipModule} from '@angular/material/tooltip';
import {RouterModule} from '@angular/router';
import {TranslateModule} from '@ngx-translate/core';
import {DefaultPageMeta} from 'app/models/shared';
import {TransactionFilter, TransactionLog} from 'app/models/transaction';
import {TransactionService} from 'app/services/transaction.service';
import {DateFormatPipe} from 'app/pipes/date_format.pipe';
import {ByteFormatPipe} from 'app/pipes/format_bytes.pipe';
import Chart from 'chart.js/auto';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import 'chartjs-adapter-moment';
import moment from 'moment';
import Zoom from 'chartjs-plugin-zoom';
import {FormaterService} from 'app/services/formater.service';
import {MatTabsModule} from '@angular/material/tabs';
import {MatDatepickerModule} from '@angular/material/datepicker';
import {MatButtonToggleModule} from '@angular/material/button-toggle';
import {MatGridListModule} from '@angular/material/grid-list';
import {MatExpansionModule} from '@angular/material/expansion';
import {animate, state, style, transition, trigger} from '@angular/animations';
import {TimeFormatPipe} from 'app/pipes/format_time.pipe';
import {TransactionRAWDialogComponent} from 'app/components/transaction-raw-dialog/transaction-raw-dialog.component';
import {MatRipple} from "@angular/material/core";
import {RuleDetailsDialogComponent} from "../../components/rule-details-dialog/rule-details-dialog.component";
import {RuleService} from "../../services/sensor.service";
import {MatSnackBar} from '@angular/material/snack-bar';
import {MatSnackBarModule} from '@angular/material/snack-bar';
import {HighlightModule} from 'ngx-highlightjs';
import {HighlightLineNumbers} from 'ngx-highlightjs/line-numbers';
import {DatetimeFieldComponent} from '../../components/datetime-field/datetime-field.component';

@Component({
    selector: 'app-transaction-list',
    standalone: true,
    animations: [
        trigger('detailExpand', [
            state('collapsed', style({height: '0px', minHeight: '0'})),
            state('isExpanded', style({height: '*'})),
            transition(
                'isExpanded <=> collapsed',
                animate('225ms cubic-bezier(0.4, 0.0, 0.2, 1)')
            )
        ])
    ],
    imports: [RouterModule, CommonModule, MatButtonToggleModule,
        ReactiveFormsModule, TranslateModule, MatTabsModule, MatDatepickerModule,
        MatMomentDateModule, ByteFormatPipe, DateFormatPipe, TimeFormatPipe,
        MatSidenavModule, MatIconModule, MatButtonModule, MatGridListModule,
        MatListModule, MatCardModule, MatProgressBarModule, MatInputModule,
        MatTableModule, MatMenuModule, MatSortModule, MatExpansionModule,
        MatTooltipModule, MatSelectModule, MatPaginatorModule, MatSlideToggleModule,
        MatFormFieldModule, MatChipsModule, MatRipple, FormsModule, MatSnackBarModule,
        DatetimeFieldComponent],
    templateUrl: './transaction-list.component.html',
    styleUrl: './transaction-list.component.css',
})

export class TransactionListComponent implements OnInit {
    @ViewChild('startField') startField: any;
    @ViewChild('endField') endField: any;

    readonly panelOpenState = signal(false);
    input_regex: string = "";
    logtime_start: Date = moment().subtract(1, 'day').toDate();
    logtime_end: Date = moment().toDate();
    form = new FormGroup({
        start: new FormControl<Date>(moment().subtract(1, 'day').toDate()),
        end: new FormControl<Date>(moment().toDate()),
        filters: new FormControl<Array<string>>([]),
    });

    transactionDC: string[] = ['logtime', 'score', 'source', 'service', 'request_line', 'duration', 'expand'];
    transactionDS: MatTableDataSource<TransactionLog>;
    transactionPA = new DefaultPageMeta();
    transactions: Array<TransactionLog> = [];
    currentRowSelected: TransactionLog = {} as TransactionLog;

    chart: any;
    chartConfig = {
        type: 'line',
        plugins: [ChartDataLabels],
        data: {
            labels: [],
            datasets: [
                {
                    label: "TPM",
                    data: [],
                    backgroundColor: 'limegreen'
                }
            ]
        },
        options: {
            layout: {
                padding: 5
            },
            aspectRatio: 1.5,
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                datalabels: {
                    display: false
                },
                zoom: {
                    zoom: {
                        drag: {
                            enabled: true
                        },
                        mode: 'x',
                        onZoomComplete: (chartUpdate: any) => {
                            const xAxis = chartUpdate['chart'].scales['x'];
                            this.form.get('start')?.setValue(xAxis.min);
                            this.form.get('end')?.setValue(xAxis.max);
                            this.onSearch();
                        },
                    }
                }
            },
            scales: {
                x: {
                    type: 'time',
                    ticks: {
                        autoSkip: true,
                        autoSkipPadding: 50,
                        maxRotation: 0
                    },
                    time: {
                        unit: 'day',
                        displayFormats: {
                            day: 'dd',
                            hour: 'HH:mm',
                            minute: 'HH:mm',
                            second: 'HH:mm:ss'
                        }
                    }
                },
                y: {
                    ticks: {
                        callback: (value: any) => {
                            return this.formatService.tpm(value);
                        }
                    },
                    beginAtZero: true,
                }
            }
        },
    } as any;

    constructor(
        private transactionService: TransactionService,
        private confirmDialog: MatDialog,
        private responsive: BreakpointObserver,
        private formatService: FormaterService,
        private ruleService: RuleService,
        private snackBar: MatSnackBar
    ) {
        Chart.register(ChartDataLabels);
        Chart.register(Zoom);
        this.transactionDS = new MatTableDataSource<TransactionLog>;
        this.responsive.observe([Breakpoints.Small])
            .subscribe(result => {
                if (result.breakpoints[Breakpoints.Small]) {
                    this.transactionDC = ['logtime', 'source', 'service', 'request_line', 'expand'];
                }
            });
    }

    expandCollapse(row: any) {
        if (this.currentRowSelected && this.currentRowSelected != row)
            this.currentRowSelected.isExpanded = false;
        this.currentRowSelected = row;

        if (row.isExpanded) {
            row.isExpanded = false;
        } else {
            row.isExpanded = true;
        }
    }

    ngOnInit(): void {
        this.onSearch();
    }

    onSearch() {
        let filter = this.form.value as TransactionFilter;
        this.transactionService.getTpm(filter).subscribe(data => {
            if (this.chart != null) {
                this.chart.destroy();
            }
            ;
            this.chart = new Chart("trn-chart", this.chartConfig);
            this.chart.data.labels = [];
            this.chart.data.datasets[0].data = [];
            for (let i = 0; i < data.length; i++) {
                this.chart.data.labels.push(moment(data[i].logtime));
                this.chart.data.datasets[0].data.push(data[i].count);
            }
            this.chart.update();
        });

        this.transactionService.search(filter, this.transactionPA).subscribe(data => {
            this.transactions = data.data;
            this.transactionDS.data = data.data;
            if (data.metadata) {
                this.transactionPA = data.metadata;
            } else {
                this.transactionPA = new DefaultPageMeta();
            }
        });
    }

    nextPage(event: PageEvent) {
        this.transactionPA.page = event.pageIndex + 1;
        this.transactionPA.per_page = event.pageSize;
        this.onSearch();
    }

    resolveClass(code: number) {
        if ([200, 201, 202, 301, 302].includes(code)) {
            return "allow";
        }
        if ([404, 401].includes(code)) {
            return "warn";
        }
        return "deny";
    }

    onShowRAW(trn: TransactionLog) {
        this.confirmDialog.open(TransactionRAWDialogComponent, {
            data: trn
        });
    }

    onShowRuleDetails(rule_code: number) {
        this.ruleService.get_by_code(rule_code).subscribe(data => {
            this.confirmDialog.open(RuleDetailsDialogComponent, {
                data: data
            });
        });
    }

    ngAfterViewInit(): void {
        this.responsive.observe([Breakpoints.Small])
            .subscribe(result => {
                if (this.chart) {
                    if (result.breakpoints[Breakpoints.Small]) {
                        this.chart.options.aspectRatio = 2.5;
                    }
                    this.chart.update();
                }
            });
    }

    onAddFilter(): void {
        if (!this.input_regex.trim()) {
            return;
        }
        try {
            const filter = JSON.parse(this.input_regex);
            if (typeof filter !== 'object' || filter === null) {
                throw new Error('Filter must be a JSON object');
            }
            if (this.form.value.filters != null) {
                const existingFilters = this.form.value.filters.map(f => JSON.parse(f));
                const newKeys = Object.keys(filter);
                
                for (const existingFilter of existingFilters) {
                    const existingKeys = Object.keys(existingFilter);
                    const duplicates = newKeys.filter(key => existingKeys.includes(key));
                    
                    if (duplicates.length > 0) {
                        throw new Error(`Duplicate keys found: ${duplicates.join(', ')}`);
                    }
                }

                this.form.value.filters.push(JSON.stringify(filter));
            }
            this.input_regex = "";
        } catch (error: unknown) {
            const errorMessage = error instanceof Error ? error.message : 'Invalid filter format. Please enter a valid JSON object.';
            this.snackBar.open(
                errorMessage,
                'Close', 
                {
                    duration: 5000,
                    horizontalPosition: 'center',
                    verticalPosition: 'bottom',
                }
            );
        }
    }

    onRemoveFilter(keyword: any): void {
        if (this.form.value.filters != null) {
            let index = this.form.value.filters.indexOf(keyword);
            if (index >= 0) {
                this.form.value.filters.splice(index, 1);
            }
        }
    }

    onDateTimeConfirm(event: any,form_field: string) {
        this.form.get(form_field)?.setValue(event.toDate());
    }
}