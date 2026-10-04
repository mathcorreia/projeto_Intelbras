import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CameraAddComponent } from './camera-add.component';

describe('CameraAddComponent', () => {
  let component: CameraAddComponent;
  let fixture: ComponentFixture<CameraAddComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CameraAddComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CameraAddComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
