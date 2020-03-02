//******************************************************************************
//   MSP430G2xx3 Demo - USCI_B0, I2C Master multiple byte TX/RX
//
//   Description: I2C master communicates to I2C slave sending and receiving
//   3 different messages of different length. I2C master will enter LPM0 mode
//   while waiting for the messages to be sent/receiving using I2C interrupt.
//   ACLK = NA, MCLK = SMCLK = DCO 16MHz.
//
//
//                   MSP430G2553         3.3V
//                 -----------------   /|\ /|\
//            /|\ |                 |   |  4.7k
//             |  |                 |  4.7k |
//             ---|RST              |   |   |
//                |                 |   |   |
//                |             P1.6|---|---+- I2C Clock (UCB0SCL)
//                |                 |   |
//                |             P1.7|---+----- I2C Data (UCB0SDA)
//                |                 |
//                |                 |
//
//   Nima Eskandari
//   Texas Instruments Inc.
//   April 2017
//   Built with CCS V7.0
//******************************************************************************

#include <msp430.h>
#include <stdint.h>
#include <stdbool.h>

//******************************************************************************
// Example Commands ************************************************************
//******************************************************************************

#define SLAVE_ADDR  0x2c

#define TXD BIT2
#define RXD BIT1
#define LF 10
#define CR 13
#define MAX_BUFFER_SIZE     20

volatile char d[5];
unsigned char *current_value = 0x1000;

//*****************************************************************************
//RDAC Registers **************************************************************
//*****************************************************************************

uint8_t SelectR1 [1] = { 0x00};
uint8_t SelectR2 [1] = { 0x80};

//******************************************************************************
//RDAC Data - Values for Resistors *********************************************
//******************************************************************************
uint8_t SetR2 [1] = { 0x31};


uint8_t SetR1_1_2 [1] = { 0x19}; //1.2V
uint8_t SetR1_1_5 [1] = { 0x2B}; //1.5V
uint8_t SetR1_2_4 [1] = { 0x63}; //2.4V
uint8_t SetR1_3_0 [1] = { 0x89}; //3.0V
uint8_t SetR1_3_7 [1] = { 0xB3}; //3.7V
uint8_t SetR1_4_2 [1] = { 0xD2}; //4.2V
uint8_t SetR1_4_5 [1] = { 0xE4}; //4.5V




//******************************************************************************
//RDAC Data - Values for WriteReg **********************************************
//******************************************************************************
uint8_t Reg_Data [1] = { 0x00};


//******************************************************************************
//RDAC Data - Values for INA233 **********************************************
//******************************************************************************
uint8_t INA_D0 [2] = { 0x05,0x40 };
//uint8_t INA_D0 [2] = { 0x25,0x42 }; //set parameters for INA233 D0h register MFR_ADC_CONFIG
uint8_t INA_D4 [2] = { 0x01,0x00 };

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
uint8_t ReceiveBuffer[MAX_BUFFER_SIZE] = {0};
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
void CopyArray(uint8_t *source, uint8_t *dest, uint8_t count);

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

void CopyArray(uint8_t *source, uint8_t *dest, uint8_t count)
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
void capture_i(void);
void erase_SegCD(void);


//******************************************************************************
// Device Initialization *******************************************************
//******************************************************************************

void initClockTo16MHz()
{
    if (CALBC1_16MHZ==0xFF)                  // If calibration constant erased
    {
        while(1);                               // do not load, trap CPU!!
    }
    DCOCTL = 0;                               // Select lowest DCOx and MODx settings
    BCSCTL1 = CALBC1_16MHZ;                    // Set DCO
    DCOCTL = CALDCO_16MHZ;
}

void initGPIO()
{
  //  P1DIR |= BIT0 + BIT1 + BIT2 + BIT3 + BIT4;
  //  P1OUT &= ~(BIT0 + BIT1 + BIT2 + BIT3 + BIT4);
    P1SEL  |= RXD + TXD;
    P1SEL2 |= RXD + TXD;          //Assign pins 1.1 RX and 1.2 TX

    P1SEL |= BIT6 + BIT7;                     // Assign I2C pins to USCI_B0
    P1SEL2|= BIT6 + BIT7;                     // Assign I2C pins to USCI_B0
}

void initI2C()
{
    UCB0CTL1 |= UCSWRST;                      // Enable SW reset
    UCB0CTL0 = UCMST + UCMODE_3 + UCSYNC;     // I2C Master, synchronous mode
    UCB0CTL1 = UCSSEL_2 + UCSWRST;            // Use SMCLK, keep SW reset
    UCB0BR0 = 160;                            // fSCL = SMCLK/160 = ~100kHz
    UCB0BR1 = 0;
    UCB0I2CSA = SLAVE_ADDR;                   // Slave Address
    UCB0CTL1 &= ~UCSWRST;                     // Clear SW reset, resume operation
    UCB0I2CIE |= UCNACKIE;
}

void uartInit()
{
    /*** UART Set-Up ***/
       UCA0CTL1 |= UCSSEL_2;         // SMCLK
      // UCA0BR0 = 138;               // 16MHz/138 ~115200
      // UCA0BR0 = 0x8A;
      // UCA0BR1 = 0x00;
       UCA0BR0 = 78;
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
    P2SEL &= (~BIT1);   // Set P2.1 SEL for GPIO
    P2SEL2 &= (~BIT1);  // Set P2.1 SEL for GPIO
    P2DIR &= (~BIT1);   // Set P2.1 as Input

    P2REN |= BIT1;      // Enable internal pull-up/down resistors
    P2OUT &= (~BIT1);   // Set as  pull down resistor

    P2IE |= BIT1;     // P2.1 interrupt enabled
    P2IES &= ~BIT1;    // P2.1 LO/HI edge
    P2IFG &= ~BIT1;    // P2.1 IFG cleared

    I2C_Master_WriteReg(0x40, 0xD0, INA_D0, 0x02);

  //  _BIS_SR(CPUOFF + GIE);        // Enter LPM0 w/ interrupt
    __enable_interrupt();

     while(1){

         while(TXMode == TRANSMIT){
                         I2C_Master_WriteReg(0x40, 0xD1, Reg_Data, 0x01); //write the desired command that is to return the value
                         I2C_Master_ReadReg(0x40, 0xD1, 2);
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
       int i =0;

       switch(inp)
       {
           case 'a': //Set Output to 1.2V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2 , 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_1_2, 0x01);
           break;

           case 'b':  // Set Output to 1.5V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2, 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_1_5, 0x01);
           break;

           case 'c': //Set Output to 2.4V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2 , 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_2_4, 0x01);
           break;

           case 'd':  // Set Output to 3.0V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2, 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_3_0, 0x01);
           break;

           case 'e': //Set Output to 3.7V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2 , 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_3_7, 0x01);
           break;

           case 'f':  // Set Output to 4.2V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2, 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_4_2, 0x01);
           break;

           case 'g':  // Set Output to 4.5V
                I2C_Master_WriteReg(SLAVE_ADDR, 0x00,SetR2, 0x01);
                I2C_Master_WriteReg(SLAVE_ADDR, 0x80, SetR1_4_5, 0x01);
           break;

           case 'h':
               P2OUT |= BIT0; // Set P2.0 HIGH
           break;

           case 'i':
               P2OUT &= (~BIT0);   // Set P2.0 LOW
           break;

           case 'j':
        	   I2C_Master_WriteReg(0x40, 0xD4, INA_D4, 0x02);

        	   I2C_Master_WriteReg(0x40, 0xD4, Reg_Data, 0x01); //write the desired command that is to return the value
               I2C_Master_ReadReg(0x40, 0xD4, 2);
               CopyArray(ReceiveBuffer, data, 2);

               while(!(IFG2 & UCA0TXIFG));
               UCA0TXBUF = (char) data[1];      // 0xD1 INA233 Vshunt register MSB
               while(!(IFG2 & UCA0TXIFG));      // 0xD1 INA233 Vshunt register LSB
               UCA0TXBUF = (char) data[0];
           break;

           case 'x':
               P2IE |= BIT1;       // P2.1 interrupt enabled
           break;

           case 'y':
                TXMode=IDLE;
           break;

           case 'z':
               P2IE &= (~BIT1);   // P2.1 interrupt disabled
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

// Port 2 interrupt service routine
#pragma vector=PORT2_VECTOR
__interrupt void Port_2(void)
{

   if (TXMode == IDLE) {

       TXMode = TRANSMIT;  // Start capture mode
   }

   else {
       while(!(IFG2 & UCA0TXIFG));
       UCA0TXBUF = 0x00;             // 0xD1 INA233 Vshunt register MSB
       while(!(IFG2 & UCA0TXIFG));   // 0xD1 INA233 Vshunt register LSB
       UCA0TXBUF = 0x00;
       delay(10000);
       TXMode = IDLE;     // Stop capture mode
   }

   P2IES ^=  BIT1;        // P2.1 LO/HI edge
   P2IFG &= ~BIT1;        // P2.1 IFG cleared
}
