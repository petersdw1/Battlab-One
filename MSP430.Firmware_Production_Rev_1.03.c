//******************************************************************************
//   MSP430G2xx3 based BattLab1_Pre-Release
//
//   Doug Peters
//   Bluebird Labs LLC.
//   www.bluebird-labs.com
//   February 2019
//   Built with CCS V7.0
//******************************************************************************

#include <msp430.h>
#include <stdint.h>
#include <stdbool.h>

//******************************************************************************
// #Defines ************************************************************
//******************************************************************************
//i2c Addresses
#define INA233_ADDR  0x40  //INA233
#define AD5248_ADDR  0x2c  //AD5248

#define R1_ADDR  0x80  //RDAC Resistor1 Register Addresses
#define R2_ADDR  0x00  //RDAC Resistor2 Register Addresses

//UART
#define TXD BIT2
#define RXD BIT1
#define LF 10
#define CR 13
#define MAX_BUFFER_SIZE     20

volatile char d[5];

//******************************************************************************
//INA233 Data **********************************************
//******************************************************************************
uint8_t INA233_1_D0 [2] = { 0x05,0x40 }; ///set parameters for INA233 D0h register MFR_ADC_CONFIG
uint8_t INA233_4_D0 [2] = { 0x15,0x43 }; ///set parameters for INA233 D0h register MFR_ADC_CONFIG
uint8_t INA233_16_D0 [2] = { 0x15,0x45 }; ///set parameters for INA233 D0h register MFR_ADC_CONFIG
uint8_t INA233_64_D0 [2] = { 0x15,0x47 }; ///set parameters for INA233 D0h register MFR_ADC_CONFIG


//uint8_t INA_D4 [2] = { 0x68,0x06 }; ///MFR CAL for active mode
//uint8_t INA1_D4 [2] = { 0x81,0x00 }; ///MFR CAL for sleep mode

uint8_t INA_D4 [2] = { 0x55,0x0D }; ///MFR CAL for active mode
uint8_t INA1_D4 [2] = { 0x89,0x41 }; ///MFR CAL for sleep mode


//******************************************************************************
//AD5248 Digital Potentiometer Data
//******************************************************************************

//Resistor Values for Adj Voltage Regulator
uint8_t SetR2 [1] = { 0x31};

uint8_t SetR1_1_2 [1] = { 0x19}; //1.2V
uint8_t SetR1_1_5 [1] = { 0x2B}; //1.5V
uint8_t SetR1_2_4 [1] = { 0x63}; //2.4V
uint8_t SetR1_3_0 [1] = { 0x89}; //3.0V
uint8_t SetR1_3_2 [1] = { 0x98}; //3.2V
uint8_t SetR1_3_6 [1] = { 0xAB}; //3.6V
uint8_t SetR1_3_7 [1] = { 0xB1}; //3.7V
uint8_t SetR1_4_2 [1] = { 0xD2}; //4.2V
uint8_t SetR1_4_5 [1] = { 0xE4}; //4.5V


//******************************************************************************
//Calibration Factors *********************************************
//******************************************************************************

// Active current resistor calibration
#define VERSION_MSB 0x03;
#define VERSION_LSB 0xEB;

#define CAL_12_MSB 0x01;
#define CAL_12_LSB 0x3B;

#define CAL_15_MSB 0x00;
#define CAL_15_LSB 0xE1;

#define CAL_24_MSB 0x00;
#define CAL_24_LSB 0xB5;

#define CAL_30_MSB 0x00;
#define CAL_30_LSB 0xAE;

#define CAL_32_MSB 0x00;
#define CAL_32_LSB 0xAE;

#define CAL_36_MSB 0x00;
#define CAL_36_LSB 0xAA;

#define CAL_37_MSB 0x00;
#define CAL_37_LSB 0xA8;

#define CAL_42_MSB 0x00;
#define CAL_42_LSB 0xA5;

#define CAL_45_MSB 0x00;
#define CAL_45_LSB 0xA1;

// Sleep current offset factors
#define OFFSET_12_MSB 0x00;
#define OFFSET_12_LSB 0x82;

#define OFFSET_15_MSB 0x00;
#define OFFSET_15_LSB 0xFA;

#define OFFSET_24_MSB 0x01;
#define OFFSET_24_LSB 0x04;

#define OFFSET_30_MSB 0x01;
#define OFFSET_30_LSB 0x18;

#define OFFSET_32_MSB 0x01;
#define OFFSET_32_LSB 0x18;

#define OFFSET_36_MSB 0x03;
#define OFFSET_36_LSB 0x30;

#define OFFSET_37_MSB 0x03;
#define OFFSET_37_LSB 0x34;

#define OFFSET_42_MSB 0x03;
#define OFFSET_42_LSB 0x6B;

#define OFFSET_45_MSB 0x03;
#define OFFSET_45_LSB 0xB6;


//******************************************************************************
//RDAC Data - Values for WriteReg **********************************************
//******************************************************************************
uint8_t Reg_Data [1] = { 0x00};


//******************************************************************************
// General I2C State Machine ***************************************************
//******************************************************************************

typedef enum I2C_ModeEnum{
    IDLE_MODE,
    NACK_MODE,
    TX_REG_ADDRESS_MODE,
    RX_REG_ADDRESS_MODE,
    TX_DATA_MODE,
    RX_DATA_MODE,
    SWITCH_TO_RX_MODE,
    SWITHC_TO_TX_MODE,
    TIMEOUT_MODE
} I2C_Mode;

typedef enum Transmit_ModeEnum{
    IDLE,
    TRANSMIT
} Transmit_Mode;

/* Used to track the state of the software state machine*/
I2C_Mode MasterMode = IDLE_MODE;
Transmit_Mode TXMode = IDLE;

/* The Register Address/Command to use*/
uint8_t TransmitRegAddr = 0;

/* ReceiveBuffer: Buffer used to receive data in the ISR
 * RXByteCtr: Number of bytes left to receive
 * ReceiveIndex: The index of the next byte to be received in ReceiveBuffer
 * TransmitBuffer: Buffer used to transmit data in the ISR
 * TXByteCtr: Number of bytes left to transfer
 * TransmitIndex: The index of the next byte to be transmitted in TransmitBuffer
 * */
volatile uint8_t ReceiveBuffer[MAX_BUFFER_SIZE] = {0};
volatile  uint8_t data[MAX_BUFFER_SIZE] = {0};
uint8_t RXByteCtr = 0;
uint8_t ReceiveIndex = 0;
uint8_t TransmitBuffer[MAX_BUFFER_SIZE] = {0};
uint8_t TXByteCtr = 0;
uint8_t TransmitIndex = 0;

/* I2C Write and Read Functions */

/* For slave device with dev_addr, writes the data specified in *reg_data
 *
 * dev_addr: The slave device address.
 *           Example: SLAVE_ADDR
 * reg_addr: The register or command to send to the slave.
 *           Example: CMD_TYPE_0_MASTER
 * *reg_data: The buffer to write
 *           Example: MasterType0
 * count: The length of *reg_data
 *           Example: TYPE_0_LENGTH
 *  */
I2C_Mode I2C_Master_WriteReg(uint8_t dev_addr, uint8_t reg_addr, uint8_t *reg_data, uint8_t count);

/* For slave device with dev_addr, read the data specified in slaves reg_addr.
 * The received data is available in ReceiveBuffer
 *
 * dev_addr: The slave device address.
 *           Example: SLAVE_ADDR
 * reg_addr: The register or command to send to the slave.
 *           Example: CMD_TYPE_0_SLAVE
 * count: The length of data to read
 *           Example: TYPE_0_LENGTH
 *  */
I2C_Mode I2C_Master_ReadReg(uint8_t dev_addr, uint8_t reg_addr, uint8_t count);
void CopyArray(volatile uint8_t *source, volatile uint8_t *dest, uint8_t count);

I2C_Mode I2C_Master_ReadReg(uint8_t dev_addr, uint8_t reg_addr, uint8_t count)
{
    /* Initialize state machine */
    MasterMode = TX_REG_ADDRESS_MODE;
    TransmitRegAddr = reg_addr;
    RXByteCtr = count;
    TXByteCtr = 0;
    ReceiveIndex = 0;
    TransmitIndex = 0;

    /* Initialize slave address and interrupts */
    UCB0I2CSA = dev_addr;
    IFG2 &= ~(UCB0TXIFG + UCB0RXIFG);       // Clear any pending interrupts
    IE2 &= ~UCB0RXIE;                       // Disable RX interrupt
    IE2 |= UCB0TXIE;                        // Enable TX interrupt

    UCB0CTL1 |= UCTR + UCTXSTT;             // I2C TX, start condition
    __bis_SR_register(CPUOFF + GIE);              // Enter LPM0 w/ interrupts

    return MasterMode;

}

I2C_Mode I2C_Master_WriteReg(uint8_t dev_addr, uint8_t reg_addr, uint8_t *reg_data, uint8_t count)
{
    /* Initialize state machine */
    MasterMode = TX_REG_ADDRESS_MODE;
    TransmitRegAddr = reg_addr;

    //Copy register data to TransmitBuffer
    CopyArray(reg_data, TransmitBuffer, count);

    TXByteCtr = count;
    RXByteCtr = 0;
    ReceiveIndex = 0;
    TransmitIndex = 0;

    /* Initialize slave address and interrupts */
    UCB0I2CSA = dev_addr;
    IFG2 &= ~(UCB0TXIFG + UCB0RXIFG);       // Clear any pending interrupts
    IE2 &= ~UCB0RXIE;                       // Disable RX interrupt
    IE2 |= UCB0TXIE;                        // Enable TX interrupt

    UCB0CTL1 |= UCTR + UCTXSTT;             // I2C TX, start condition
    __bis_SR_register(CPUOFF + GIE);              // Enter LPM0 w/ interrupts

    return MasterMode;
}

void CopyArray(volatile uint8_t *source, volatile uint8_t *dest, uint8_t count)
{
    uint8_t copyIndex = 0;
    for (copyIndex = 0; copyIndex < count; copyIndex++)
    {
        dest[copyIndex] = source[copyIndex];
    }
}

void uartInit(void);
void bin2bcd(unsigned int v);
void putc(unsigned char c);


//******************************************************************************
// Device Initialization *******************************************************
//******************************************************************************

void initClockTo16MHz()
{
    if (CALBC1_16MHZ==0xFF)             // 16MHz
    {
        while(1);                               // do not load, trap CPU!!
    }
    DCOCTL = 0;                               // Select lowest DCOx and MODx settings
    BCSCTL1 = CALBC1_16MHZ;                    // Set DCO
    DCOCTL = CALDCO_16MHZ;               // 16MHz
}

void initGPIO()
{
    P1SEL  |= RXD + TXD;
    P1SEL2 |= RXD + TXD;          //Assign pins 1.1 RX and 1.2 TX

    P1SEL |= BIT6 + BIT7;         // Assign I2C pins to USCI_B0
    P1SEL2|= BIT6 + BIT7;        // Assign I2C pins to USCI_B0
}

void initI2C()
{
    UCB0CTL1 |= UCSWRST;                      // Enable SW reset
    UCB0CTL0 = UCMST + UCMODE_3 + UCSYNC;     // I2C Master, synchronous mode
    UCB0CTL1 = UCSSEL_2 + UCSWRST;            // Use SMCLK, keep SW reset
    UCB0BR0 = 160;                            // fSCL = SMCLK/160 = ~100kHz
    UCB0BR1 = 0;
    UCB0I2CSA = AD5248_ADDR;                   // Slave Address
    UCB0CTL1 &= ~UCSWRST;                     // Clear SW reset, resume operation
    UCB0I2CIE |= UCNACKIE;
}

void uartInit()
{
    /*** UART Set-Up ***/
       UCA0CTL1 |= UCSSEL_2;         // SMCLK
       UCA0BR0 = 138;    // ~115200 baud
       UCA0BR1 = 0;

       UCA0MCTL = UCBRS2 + UCBRS0;        // Modulation UCBRSx = 5
       UCA0CTL1 &= ~UCSWRST;              // **Initialize USCI state machine**
       UC0IE |= UCA0TXIE;                 // Enable USCI_A0 TX interrupt
       IE2=UCA0TXIE;            // Enable USCI_A0 RX interrupt
       IE2=UCA0RXIE;            // Enable USCI_A0 RX interrupt
}

void putc(unsigned char c)
{
  while (!(IFG2 & UCA0TXIFG));
  UCA0TXBUF = c;
}

void bin2bcd(unsigned int v)
{
 unsigned int var;

 for (var = 0; var < 6; var++)
     { d[var] = v % 10;
     v=v/10; }
}

void delay_ms(unsigned int ms)
{
    while (ms)
    {
        __delay_cycles(16000);
        ms--;
    }
}

void delay(unsigned long d)
{
  unsigned long delay;
  for (delay = 0; delay < d; delay++);
}


//******************************************************************************
// Main ************************************************************************
// *****************************************************************************
//******************************************************************************

int main(void) {

     WDTCTL = WDTPW | WDTHOLD;     // Stop watchdog timer

    initClockTo16MHz();
    initGPIO();
    uartInit();                  // Initialize UART
    initI2C();

// USE Pin 2.0 for turning Voltage output ON/OFF
    P2SEL &= (~BIT0);  // Set P2.0 SEL for GPIO
    P2SEL2 &= (~BIT0); // Set P2.0 SEL for GPIO
    P2DIR |= BIT0;    // Set P2.0 as Output
    P2OUT &= (~BIT0); // Set P2.0 LOW

//Use Pin 2.1 for Trigger start
     P2IFG &= ~BIT1;    // P2.1 IFG cleared
     P2SEL &= (~BIT1);   // Set P2.1 SEL for GPIO
     P2SEL2 &= (~BIT1);  // Set P2.1 SEL for GPIO
     P2DIR &= (~BIT1);   // Set P2.1 as Input

     P2REN |= BIT1;      // Enable internal pull-up/down resistors
     P2OUT &= (~BIT1);   // Set as  pull down resistor

     P2IES &= ~BIT1;    // P2.1 LO/HI edge
     P2IFG &= ~BIT1;    // P2.1 IFG cleared
   //P2IE |= BIT1;     // P2.1 interrupt enabled
     P2IE &= (~BIT1);   // P2.1 interrupt disabled

 // USE Pin 2.2 for turning ON/OFF sleep current Sense Resistor
     P2SEL &= (~BIT2);  // Set P2.2 SEL for GPIO
     P2SEL2 &= (~BIT2); // Set P2.2 SEL for GPIO
     P2DIR |= BIT2;    // Set P2.2 as Output
     P2OUT |= BIT2; // Set P2.2 LOW - Turn Low Current Sense Resistor Off

    delay_ms(100); //Delay waiting so secondary side of power rail can power up

    I2C_Master_WriteReg(INA233_ADDR, 0xD0, INA233_4_D0, 0x02);
    I2C_Master_WriteReg(INA233_ADDR, 0xD4, INA_D4, 0x02);

  //  _BIS_SR(CPUOFF + GIE);        // Enter LPM0 w/ interrupt
    __enable_interrupt();

     while(1){

         while(TXMode == TRANSMIT){
                         I2C_Master_WriteReg(INA233_ADDR, 0xD1, Reg_Data, 0x01); //write the desired command that is to return the value
                         I2C_Master_ReadReg(INA233_ADDR, 0xD1, 2);
                        // I2C_Master_WriteReg(INA233_ADDR, 0x89, Reg_Data, 0x01); //write the desired command that is to return the value
                        // I2C_Master_ReadReg(INA233_ADDR, 0x89, 2);
                         CopyArray(ReceiveBuffer, data, 2);

                         while(!(IFG2 & UCA0TXIFG));
                         UCA0TXBUF = (char) data[1];      // 0xD1 INA233 Vshunt register MSB
                         while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
                         UCA0TXBUF = (char) data[0];
                         }
    }

}


//******************************************************************************
// I2C Interrupt For Received and Transmitted Data ALSO FOR UART TX******************************
//******************************************************************************

#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector = USCIAB0TX_VECTOR
__interrupt void USCIAB0TX_ISR(void)
#elif defined(__GNUC__)
void __attribute__ ((interrupt(USCIAB0TX_VECTOR))) USCIAB0TX_ISR (void)
#else
#error Compiler not supported!
#endif
{
  if (IFG2 & UCB0RXIFG)                 // Receive I2C Data Interrupt
  {
      //Must read from UCB0RXBUF
      uint8_t rx_val = UCB0RXBUF;

      if (RXByteCtr)
      {
          ReceiveBuffer[ReceiveIndex++] = rx_val;
          RXByteCtr--;
      }

      if (RXByteCtr == 1)
      {
          UCB0CTL1 |= UCTXSTP;
      }
      else if (RXByteCtr == 0)
      {
          IE2 &= ~UCB0RXIE;
          MasterMode = IDLE_MODE;
          __bic_SR_register_on_exit(CPUOFF);      // Exit LPM0
      }
  }
  else if (IFG2 & UCB0TXIFG)            // Transmit I2C Data Interrupt
  {
      switch (MasterMode)
      {
          case TX_REG_ADDRESS_MODE:
              UCB0TXBUF = TransmitRegAddr;
              if (RXByteCtr)
                  MasterMode = SWITCH_TO_RX_MODE;   // Need to start receiving now
              else
                  MasterMode = TX_DATA_MODE;
                    // Continue to transmision with the data in Transmit Buffer
              break;

          case SWITCH_TO_RX_MODE:
              IE2 |= UCB0RXIE;              // Enable RX interrupt
              IE2 &= ~UCB0TXIE;             // Disable TX interrupt
              UCB0CTL1 &= ~UCTR;            // Switch to receiver
              MasterMode = RX_DATA_MODE;    // State state is to receive data
              UCB0CTL1 |= UCTXSTT;          // Send repeated start
              if (RXByteCtr == 1)
              {
                  //Must send stop since this is the N-1 byte
                  while((UCB0CTL1 & UCTXSTT));
                  UCB0CTL1 |= UCTXSTP;      // Send stop condition
              }
              break;

          case TX_DATA_MODE:
              if (TXByteCtr)
              {
                  UCB0TXBUF = TransmitBuffer[TransmitIndex++];
                  TXByteCtr--;
              }
              else
              {
                  //Done with transmission
                  UCB0CTL1 |= UCTXSTP;     // Send stop condition
                  MasterMode = IDLE_MODE;
                  IE2 &= ~UCB0TXIE;                       // disable TX interrupt
                  __bic_SR_register_on_exit(CPUOFF);      // Exit LPM0
              }
              break;

          default:
              __no_operation();
              break;
      }

  }

      else if (IFG2 & UCA0TXIFG)            // Transmit UART Data Interrupt
      {

      }
}

//******************************************************************************
// I2C Interrupt For Start, Restart, Nack, Stop ********************************
//******************************************************************************

#if defined(__TI_COMPILER_VERSION__) || defined(__IAR_SYSTEMS_ICC__)
#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCIAB0RX_ISR(void)
#elif defined(__GNUC__)
void __attribute__ ((interrupt(USCIAB0RX_VECTOR))) USCIAB0RX_ISR (void)
#else
#error Compiler not supported!
#endif
{

    if (IFG2 & UCA0RXIFG)               // Receive UART Data Interrupt
    {
    unsigned char inp;
       inp = UCA0RXBUF;
       int i = 0;

       switch(inp)
       {
           case 'a': //Set Output to 1.2V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2 , 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_1_2, 0x01);
           break;

           case 'b':  // Set Output to 1.5V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2, 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_1_5, 0x01);
           break;

           case 'c': //Set Output to 2.4V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2 , 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_2_4, 0x01);
           break;

           case 'd':  // Set Output to 3.0V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2, 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_3_0, 0x01);
           break;

           case 'o':  // Set Output to 3.2V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2, 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_3_2, 0x01);
           break;

           case 'n':  // Set Output to 3.6V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2, 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_3_6, 0x01);
           break;

           case 'e': //Set Output to 3.7V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2 , 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_3_7, 0x01);
           break;

           case 'f':  // Set Output to 4.2V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2, 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_4_2, 0x01);
           break;

           case 'g':  // Set Output to 4.5V
                I2C_Master_WriteReg(AD5248_ADDR, R2_ADDR,SetR2, 0x01);
                I2C_Master_WriteReg(AD5248_ADDR, R1_ADDR, SetR1_4_5, 0x01);
           break;

           case 'h':
               P2OUT |= BIT0; // Set P2.0 HIGH Turn PSU ON
           break;

           case 'i':
               P2OUT &= (~BIT0);   // Set P2.0 LOW Turn PSU OFF
           break;

           case 'j': //Get Sense Resistor calibration values

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_12_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_12_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_15_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_15_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_24_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_24_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_30_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_30_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_36_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_36_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_37_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_37_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_42_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_42_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) CAL_45_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) CAL_45_LSB;

               ///Send Low Current calibration factors

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_12_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_12_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_15_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_15_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_24_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_24_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_30_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_30_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_32_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_32_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_36_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_36_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_37_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_37_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_42_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_42_LSB;

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) OFFSET_45_MSB;      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) OFFSET_45_LSB;

           break;

           case 'k':
               P2OUT |= BIT2; // Set P2.2 HIGH to turn ON the sleep current Sense Resistor
               I2C_Master_WriteReg(INA233_ADDR, 0xD4, INA1_D4, 0x02);
           break;

           case 'l':
               P2OUT &= (~BIT2);   // Set P2.2 LOW to turn OFF the sleep current Sense Resistor
               I2C_Master_WriteReg(INA233_ADDR, 0xD4, INA_D4, 0x02);

           break;

           case 'm': //Get CONFIG
               I2C_Master_WriteReg(INA233_ADDR, 0xD4, Reg_Data, 0x01); //write the desired command that is to return the value
               I2C_Master_ReadReg(INA233_ADDR, 0xD4, 2);
               CopyArray(ReceiveBuffer, data, 2);

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) data[1];      // 0xD4 INA233 register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD4 INA233 register LSB
               UCA0TXBUF = (char) data[0];

               I2C_Master_WriteReg(INA233_ADDR, 0xD0, Reg_Data, 0x01); //write the desired command that is to return the value
               I2C_Master_ReadReg(INA233_ADDR, 0xD0, 2);
               CopyArray(ReceiveBuffer, data, 2);

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) data[1];      // Send the 0xD0 INA233 register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD0 INA233  register LSB
               UCA0TXBUF = (char) data[0];

           break;

           case 's': //Set number of averages to 1
               I2C_Master_WriteReg(INA233_ADDR, 0xD0,INA233_1_D0, 0x02);
           break;

           case 't': //Set number of averages to 4
               I2C_Master_WriteReg(INA233_ADDR, 0xD0,INA233_4_D0, 0x02);
           break;

           case 'u': //Set number of averages to 16
               I2C_Master_WriteReg(INA233_ADDR, 0xD0,INA233_16_D0, 0x02);
           break;

           case 'v': //Set number of averages to 64
               I2C_Master_WriteReg(INA233_ADDR, 0xD0,INA233_64_D0, 0x02);
           break;

           case 'w': //Reboot the MSP430
               WDTCTL = 0;
           break;

           case 'p': //Send firmware version number
               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) VERSION_MSB;  // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) VERSION_LSB;
           break;

           case 'x':

               P2IE |= BIT1;       // P2.1 interrupt enabled/set trigger
               P2IES &= ~BIT1;    // P2.1 LO/HI edge triggering
           break;

           case 'y':
               P2IE &= (~BIT1);   // P2.1 interrupt disabled/stop transmitting
                TXMode=IDLE;
           break;

           case 'z':
               P2IE &= (~BIT1);   // P2.1 interrupt disabled/start transmitting
               TXMode=TRANSMIT;
           break;

            }
        }

    else if (UCB0STAT & UCNACKIFG)             // Receive I2C Data Interrupt
    {
        UCB0STAT &= ~UCNACKIFG;                     // Clear NACK Flags
    }
    if (UCB0STAT & UCSTPIFG)                        //Stop or NACK Interrupt
    {
        UCB0STAT &=
            ~(UCSTTIFG + UCSTPIFG + UCNACKIFG);     //Clear START/STOP/NACK Flags
    }
    else if (UCB0STAT & UCSTTIFG)
    {
        UCB0STAT &= ~(UCSTTIFG);                    //Clear START Flags
    }
}

// Port 2 Trigger Interrupt Service Routine
#pragma vector=PORT2_VECTOR
__interrupt void Port_2(void)
{
  int cntr;

  for (cntr=0;cntr<100;cntr++){

      if (cntr=99){

       if (TXMode == IDLE) {

           TXMode = TRANSMIT;  // Start capture mode
       }

       else {
       while(!(IFG2 & UCA0TXIFG));
       UCA0TXBUF = 0xFF;             // 0xD1 INA233 Vshunt register MSB
       while(!(IFG2 & UCA0TXIFG));   // 0xD1 INA233 Vshunt register LSB
       UCA0TXBUF = 0xFF;
       while(!(IFG2 & UCA0TXIFG));
       UCA0TXBUF = 0x00;             // 0xD1 INA233 Vshunt register MSB
       while(!(IFG2 & UCA0TXIFG));   // 0xD1 INA233 Vshunt register LSB
       UCA0TXBUF = 0x00;
       delay(10000);
       TXMode = IDLE;     // Stop capture mode
       }

      }
  }
   P2IES |=  BIT1;        // P2.1 HI/LO edge
   P2IFG &= ~BIT1;        // P2.1 IFG cleared
}
